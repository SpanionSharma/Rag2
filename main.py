import sys
from agent import run_agent

def main():
    print("="*50)
    print("Welcome to AutoStream AI Assistant!")
    print("Type '/exit' to end the conversation.")
    print("="*50)
    
    thread_id = "user_session_1"
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["/exit", "quit", "exit"]:
                print("Agent: Goodbye! Have a great day with AutoStream.")
                break
                
            if not user_input.strip():
                continue
                
            response = run_agent(user_input, thread_id=thread_id)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\nAgent: Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
