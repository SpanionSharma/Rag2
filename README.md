# Social-to-Lead Agentic Workflow (AutoStream)

This repository contains an AI-powered conversational agent developed for **AutoStream**, a SaaS company providing automated video editing tools. The agent is built to handle customer inquiries, classify user intent, and capture high-intent leads using a stateful agentic workflow.

## 🚀 Features

- **Intent Identification**: Automatically classifies user messages into Greetings, Inquiries, or High-Intent Leads.
- **RAG-Powered Retrieval**: Answers pricing and policy questions accurately using a local knowledge base.
- **Multi-Turn State Management**: Retains context and user details across 5-6+ conversation turns using LangGraph.
- **Lead Capture Tool**: Intelligent gathering of Name, Email, and Social Media platform before triggering a mock API call.

## 🛠️ Tech Stack

- **Language**: Python 3.9+
- **Agent Framework**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **LLM**: Google Gemini 2.5 Flash
- **Dependencies**: LangChain, Pydantic, Dotenv

## 📋 Prerequisites

1.  **Google AI API Key**: Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2.  **Environment Variable**: Set your API key in a `.env` file or export it:
    ```powershell
    $env:GOOGLE_API_KEY = "your-api-key-here"
    ```

## ⚙️ How to Run

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd service-hire
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the agent**:
    ```bash
    python main.py
    ```

---

## 🏗️ Architecture Explanation

### Why LangGraph?
I chose **LangGraph** over simple linear chains because it provides a **cyclic state machine** architecture that is essential for complex agentic behavior. Unlike basic RAG pipelines that follow a "one-and-done" flow, LangGraph allows the agent to:
1.  **Loop and Correct**: If a user provides partial information during lead capture, the agent can loop back to its own state and ask for the missing pieces. This circular logic ensures the agent has a high level of autonomy and doesn't just error out when expectations aren't met.
2.  **State Persistence**: Using `MemorySaver`, the agent maintains a specific "thread" for each user. This ensures that a pricing inquiry made ten turns ago can still inform the lead capture logic later, creating a cohesive and "living" conversation.
3.  **Explicit Control Flow**: The `StateGraph` makes the decision-making logic explicit. The flow from `classifier` -> `inquiry` vs `lead` is modular, making it easy to test each node in isolation and scale the agent by adding new capabilities without breaking existing logic.

### State Management & Leads
State is managed via a `TypedDict` that stores the message history and a structured `user_info` Pydantic model. This model tracks `name`, `email`, and `platform`. By keeping this state separate from the raw message history, the agent can quickly check which fields are missing. This architectural choice prevents "forgetfulness" in long conversations and ensures the `mock_lead_capture` tool is only invoked with a complete set of validated data, mirroring real-world backend integration requirements.

---

## 📱 WhatsApp Deployment Integration

To integrate this agent with **WhatsApp**, I would use a **Webhook-based architecture**:

1.  **Provider**: Use the **WhatsApp Business API** (via Meta or Twilio).
2.  **Middleware**: Deploy a Python/FastAPI server to act as the Webhook listener.
3.  **Flow**:
    -   User sends a message on WhatsApp.
    -   Meta/Twilio sends an HTTP POST request to our Webhook URL.
    -   The server extracts the `sender_id` (phone number) and uses it as the `thread_id` in LangGraph.
    -   The agent processes the message and generates a response.
    -   The server sends the response back to WhatsApp via a POST request to the provider's API.
4.  **Scaling**: Use a database-backed checkpointer (like PostgreSQL) for LangGraph instead of in-memory `MemorySaver` to handle multiple concurrent users across server restarts.

---

## 📑 Evaluation Criteria Met
- [x] Correct Intent Detection.
- [x] Local Knowledge Base RAG.
- [x] Multi-turn memory management.
- [x] Proper tool calling without premature execution.
- [x] Modular and clean code structure.
