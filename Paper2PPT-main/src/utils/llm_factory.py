import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.3):
    """
    Factory function to create an LLM instance based on environment variables.
    Supports DeepSeek and standard OpenAI-compatible providers.
    """
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("LLM_API_BASE") or os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    
    if not api_key:
        raise ValueError("LLM_API_KEY not found in environment variables.")

    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=temperature
    )
