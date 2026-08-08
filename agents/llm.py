import os

from langchain_groq import ChatGroq

def get_llm():
    """
    Centralized function to instantiate and return the Groq LLM client.
    Ensures that the GROQ_API_KEY is present in the environment before
    attempting to initialize ChatGroq.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # Initialize the ChatGroq client.
    # We set temperature=0 for deterministic outputs required in orchestration.
    llm = ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=0,
    )
    return llm
