import requests
import json
from datetime import date
from strands import Agent, tool
import logging
import os
from tavily import TavilyClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from strands_tools import file_read, file_write
from strands.vended_tools import file_editor
from strands.models.openai_responses import OpenAIResponsesModel
from prompts.__init__ import MODEL_CONFIG, PROMPTS,MODELS
load_dotenv()

########### SSE IMPORTS ###########
from sse.routes import getUser
from sse.redis_client import redis_client

os.environ["BYPASS_TOOL_CONSENT"] = "true"
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY"),
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def models(model_id,tier):
    return OpenAIResponsesModel(
        client_args={
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": OPENROUTER_BASE_URL,
        },
        model_id=model_id,
        params={
            "temperature": MODEL_CONFIG[tier]["temperature"],
            "max_output_tokens": MODEL_CONFIG[tier]["max_tokens"],
        },
    )

"""
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

def models(model_id, tier):
    return OpenAIResponsesModel(
        client_args={
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": GROQ_BASE_URL,
        },
        model_id=model_id,
        params={
            "temperature": MODEL_CONFIG[tier]["temperature"],
            "max_output_tokens": MODEL_CONFIG[tier]["max_tokens"],
        },
    )
"""
def send_to_frontend(data):
    user_id = getUser()
    redis_client.xadd(
            user_id,
            {
                "message": json.dumps(data)
            }
        )
    
    
    
@tool
def tavily_search(query: str) -> str:
    "Search the web for current and relevant information"
    result = tavily.search(
        query=query,
        search_depth="basic",  # advanced
        max_results=5,  # fixed: was max_result (typo, silently ignored by Tavily)
    )
    send_to_frontend({
        "type": "tool",
        "stage": "searching",
        "message": "Searching Webpage",
        "url": None
    })
    return result

@tool
def fetch_page(url: str) -> str:
    """
    Fetch web page and extract its readable text
    """
    send_to_frontend({
        "type": "tool",
        "stage": "reading",
        "message": "Reading Webpage",
        "url": url
    }) 
    
    try:
        response = requests.get(
            url, timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return text[:6000]  # Set on 5000+ just testing that's why
    except Exception as e:
        logging.error(f"Error fetching Page :{e}")
        raise
        

@tool
def update_status(
    message: str,
    stage: str = "working",
    url: str = ""
):
    """
    Send a live progress update to the current user.

    Args:
        message: Short user-visible description.
        stage: Current stage.
        url: Related URL if available.
    """
    
    send_to_frontend({
        "type": "agent_status",
        "stage": stage,
        "message": message,
        "url": url or None
    })
    return "Status sent successfully."  

############# TIER TO TIER MODELS ##############


TOOL = [tavily_search, fetch_page, file_write, file_read, file_editor,update_status]

def create_researcher_on_tier(tier):
    return Agent(
        model=models(MODELS[tier], tier),
        system_prompt=PROMPTS[tier],
        tools=TOOL
    )

