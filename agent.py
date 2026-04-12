import os
import json
from typing import TypedDict, Annotated, List, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from tools import mock_lead_capture
from dotenv import load_dotenv

load_dotenv()

# --- Internal State Definitions ---

class UserInfo(BaseModel):
    name: str = ""
    email: str = ""
    platform: str = ""

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    user_info: UserInfo
    intent: str
    next_node: str

# --- Knowledge Base Loader ---

def load_knowledge_base():
    with open("knowledge_base.json", "r") as f:
        return json.load(f)

KB_DATA = load_knowledge_base()

# --- Nodes ---

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def classifier_node(state: AgentState):
    """Classifies user intent."""
    last_message = state["messages"][-1].content
    
    prompt = f"""
    Classify the following user message into one of these intents:
    1. "greeting": Casual greetings or introductions.
    2. "inquiry": Questions about pricing, features, or policies of AutoStream.
    3. "lead": The user expresses strong interest in signing up, trying the Pro plan, or getting started.
    
    User Message: "{last_message}"
    
    Respond with ONLY the classification name (greeting, inquiry, or lead).
    """
    
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    
    # Validation against allowed types
    if intent not in ["greeting", "inquiry", "lead"]:
        intent = "inquiry"  # Default fallback
        
    return {"intent": intent, "next_node": intent}

def rag_node(state: AgentState):
    """Handles product/pricing inquiries using KB data."""
    context = json.dumps(KB_DATA, indent=2)
    last_message = state["messages"][-1].content
    history = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][:-1]])
    
    prompt = f"""
    You are an AI Sales Assistant for AutoStream. 
    Use the following Knowledge Base to answer the user's question accurately.
    
    Knowledge Base:
    {context}
    
    Conversation History:
    {history}
    
    Current User Question: "{last_message}"
    
    Guidelines:
    - Be professional and helpful.
    - If the user asks about something not in the KB, politely say you don't have that information.
    - Keep answers concise.
    """
    
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

def casual_responder_node(state: AgentState):
    """Handles greetings."""
    last_message = state["messages"][-1].content
    prompt = f"The user said '{last_message}'. Provide a friendly, brief greeting and ask how you can help them with AutoStream today."
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

def lead_capture_node(state: AgentState):
    """Handles lead information gathering and tool execution."""
    user_info = state["user_info"]
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Simple logic to extract info if present in the message
    # In a real app, we might use pydantic extraction or function calling
    # For now, we'll ask the LLM to check if Name, Email, or Platform are present in the last message or history
    
    extraction_prompt = f"""
    Given the recent user message: "{last_message}"
    And the existing info: Name={user_info.name}, Email={user_info.email}, Platform={user_info.platform}
    
    Extract any missing 'name', 'email', or 'platform' (YouTube, Instagram, etc.).
    Return a JSON object with keys "name", "email", "platform". If not found, use existing info.
    """
    
    try:
        extraction_res = llm.invoke(extraction_prompt)
        # LLM might return code blocks, we clean it
        content = extraction_res.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # Update user info if data is present
        if data.get("name"): user_info.name = data["name"]
        if data.get("email"): user_info.email = data["email"]
        if data.get("platform"): user_info.platform = data["platform"]
    except Exception:
        pass

    # Check for missing fields
    missing = []
    if not user_info.name: missing.append("name")
    if not user_info.email: missing.append("email")
    if not user_info.platform: missing.append("social media platform (e.g., YouTube)")
    
    if not missing:
        # Trigger tool
        result = mock_lead_capture(user_info.name, user_info.email, user_info.platform)
        return {
            "messages": [AIMessage(content=f"Excellent! I've captured your details. {result} One of our team members will reach out soon.")],
            "user_info": user_info
        }
    else:
        # Ask for the first missing field
        ask_prompt = f"The user wants to sign up but we are missing: {', '.join(missing)}. Politely ask for the missing information one by one, starting with the first one."
        response = llm.invoke(ask_prompt)
        return {"messages": [AIMessage(content=response.content)], "user_info": user_info}

# --- Router ---

def route_intent(state: AgentState):
    return state["next_node"]

# --- Building the Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("classifier", classifier_node)
workflow.add_node("greeting", casual_responder_node)
workflow.add_node("inquiry", rag_node)
workflow.add_node("lead", lead_capture_node)

workflow.set_entry_point("classifier")

workflow.add_conditional_edges(
    "classifier",
    route_intent,
    {
        "greeting": "greeting",
        "inquiry": "inquiry",
        "lead": "lead"
    }
)

workflow.add_edge("greeting", END)
workflow.add_edge("inquiry", END)
workflow.add_edge("lead", END) # Lead capture node can loop or end. For simplicity, we end after response.

# Use memory for state persistence
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)

def run_agent(text, thread_id="1"):
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {
        "messages": [HumanMessage(content=text)],
        "user_info": UserInfo()
    }
    
    # We yield chunks for real-time-like feel if needed, but for now just invoke
    output = agent_app.invoke(input_state, config=config)
    return output["messages"][-1].content
