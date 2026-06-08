import os
import sys
from agent_engine import AgentEngineFactory
from google.genai import types

def main():
    # 1. Verify Environment Variables
    if not os.environ.get("GEMINI_API_KEY"):
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)
        
    if not os.environ.get("GITHUB_PAT") and not os.environ.get("GITHUB_TOKEN"):
        print("[WARNING] GITHUB_PAT or GITHUB_TOKEN is not set. MCP GitHub tools may fail authentication.")

    print("[SYSTEM] Initializing Native AgentEngineFactory...")
    try:
        factory = AgentEngineFactory()
    except Exception as e:
        print(f"[ERROR] Failed to initialize factory: {e}")
        sys.exit(1)
    
    print("[SYSTEM] Compiling Spyglass Session...")
    try:
        spyglass_session = factory.compile_agent_session("Spyglass", thread_id="spyglass_github_test_001")
    except Exception as e:
        print(f"[ERROR] Failed to compile agent session: {e}")
        sys.exit(1)
        
    print("[SYSTEM] Spyglass compiled successfully. Initiating test session...\n")
    
    # 3. The Test Prompt
    test_prompt = "Hello Spyglass. Please use your tools to list the titles of the current open issues in the PirateTim/NPT-knowing-2 repository."
    print(f"USER > {test_prompt}\n")
    
    # 4. Execute the Native Chat Loop
    try:
        response = spyglass_session.send_message(test_prompt)
        
        # Handle Tool Calls natively
        while response.function_calls:
            for call in response.function_calls:
                print(f"[TOOL EXECUTION] Invoking {call.name}...")
                # Route directly to the centralized dispatcher
                tool_result = factory.dispatcher.dispatch(call)
                
                # Truncate output for console readability
                output_preview = str(tool_result)[:150].replace('\n', ' ')
                print(f"[TOOL RESULT] {output_preview}...\n")
                
                # Send the result back to the model
                response = spyglass_session.send_message(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": tool_result}
                    )
                )
                
        # Print final text response
        if response.text:
            print(f"SPYGLASS > {response.text}\n")
            
    except Exception as e:
        print(f"\n[RUNTIME ERROR] {e}")

if __name__ == "__main__":
    main()
