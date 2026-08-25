import requests
from datetime import date
from strands import Agent, tool
import logging
import os
from tavily import TavilyClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from strands_tools import file_read, file_write
from strands.vended_tools import file_editor
from strands.models.openai import OpenAIModel
from prompts.__init__ import PROMPTS,MODELS
load_dotenv()

os.environ["BYPASS_TOOL_CONSENT"] = "true"
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY"),
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
#Stone -> Level I
#Iron -> Level II
#Dimonds -> Level III
#Netherite -> Level IV

def models(model_id):
    model = OpenAIModel(
        client_args={
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": OPENROUTER_BASE_URL,
        },
        model_id=model_id,
        params={
            "temperature": 0.7,
            "max_tokens": 2000,
        },
    )
    return model
"""
# ------ New Stream Each User ------- #
import queue
import uuid
from contextvars import ContextVar

status_queues = {}

current_research_id = ContextVar(
    "current_research_id",
    default=None
)

def create_research():
    research_id = str(uuid.uuid4())
    status_queues[research_id] = queue.Queue()
    return research_id


def emit_to_frontend(data):
    research_id = current_research_id.get()

    if not research_id:
        return
    q = status_queues.get(research_id)
    if q:
        q.put(data)

def remove_research(research_id):
    status_queues.pop(research_id, None)
"""
@tool
def tavily_search(query: str) -> str:
    "Search the web for current and relevant information"
    result = tavily.search(
        query=query,
        search_depth="basic",  # advanced
        max_results=5,  # fixed: was max_result (typo, silently ignored by Tavily)
    )
    """
    emit_to_frontend({
            "type": "tool",
            "stage": "reading",
            "message": "Reading webpage",
            "url": None
        })
    """
    return result

@tool
def fetch_page(url: str) -> str:
    """
    Fetch web page and extract its readable text
    """
    """
    emit_to_frontend({
            "type": "tool",
            "stage": "reading",
            "message": "Reading webpage",
            "url": url
        })
    """
    
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
"""
@tool
def update_status(
    message: str,
    stage: str = "working",
    url: str = ""
):
    
    Send a live progress update to the current user.

    Args:
        message: Short user-visible description.
        stage: Current stage.
        url: Related URL if available.
    
    
    emit_to_frontend({
        "type": "agent_status",
        "stage": stage,
        "message": message,
        "url": url or None
    })
    
    return "Status sent successfully." 
"""  

#======================================================================================#

############# TIER TO TIER MODELS ##############

#======================================================================================#

TOOL = [tavily_search, fetch_page, file_write, file_read, file_editor]#ADD UPADTE_STATUS
def create_researcher_on_tier(tier):
    model = Agent(
        model=models(MODELS[tier]),
        system_prompt=PROMPTS[tier],
        tools=TOOL
    )
    return model



