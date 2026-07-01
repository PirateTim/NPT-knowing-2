import os
import sys
import uuid
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from react_agent.core.agent_engine import AgentEngine
from react_agent.tools.memory_tools import query_system_glossary

def chunk_text(text: str, chunk_size: int = 10000):
    """Splits a massive text file into safe, digestible chunks."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
        else:
            current_chunk += p + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def run_bulk_ingestion():
    print("=========================================================")
    print(" NPT FLEET: BULK BOOTSTRAP INGESTION (BILGELADLE) ")
    print("=========================================================")
    
    file_path = "manuscript/2026-02-24AChapters_complete.md"
    if not os.path.exists(file_path):
        print(f"[ERROR] Could not find {file_path}. Please export your Google Doc.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    chunks = chunk_text(full_text)
    print(f"[SYSTEM] Manuscript loaded. Sliced into {len(chunks)} chunks.")
    
    # Instantiate the Engine with 3.5 Flash for high-speed harvesting
    agent_name = "bilgeladle"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "react_agent", "agents", "bilgeladle", "bilgeladle.xml"))
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path, model_override="gemini-3.5-flash")
    
    # Inject the Glossary
    engine.system_instruction += f"\n\n--- CRITICAL FLEET GLOSSARY ---\n{query_system_glossary()}\n-------------------------------"
    
    thread_id = f"thread_bootstrap_{uuid.uuid4().hex[:8]}"
    chat_session = engine.start_chat_session(thread_id)
    
    print(f"[SYSTEM] Engine Online. Commencing Bulk Ingestion...\n")
    
    for i, chunk in enumerate(chunks, 1):
    # chunks[24:] skips the first 24 chunks (indices 0-23). 
    # The '25' tells enumerate to start printing to the terminal at 25.
    # for i, chunk in enumerate(chunks[24:], 25):
    # FIX: Generate a completely new thread for every single chunk
        chunk_thread_id = f"thread_bulk_{i}_{uuid.uuid4().hex[:8]}"
        chat_session = engine.start_chat_session(chunk_thread_id)
        
        prompt = f"Execute `bootstrap_ingestion` on the following text...\n\n{chunk}"
        # ... execute and save
        print(f"--- Processing Chunk {i} of {len(chunks)} ---")
        
        # Hardcode the strict mandate so it is NEVER lost
        prompt = f"Execute `bootstrap_ingestion` on the following text. Extract glossary terms to the DB, and output XML rules.\n\n{chunk}"
        
        try:
            response = engine.execute_turn(chat_session, prompt)
            print(f"\n[BILGELADLE OUTPUT]:\n{response}\n")
            engine.save_checkpoint(thread_id, chat_session.get_history())
            
            # Brief pause to prevent rate limiting on database or API
            time.sleep(2) 
            
        except Exception as e:
            print(f"[ERROR] Ingestion failed on chunk {i}: {str(e)}")
            break

    print("\n[SYSTEM] Bulk Ingestion Complete. Check cargo.system_glossary for new terms.")

if __name__ == "__main__":
    run_bulk_ingestion()