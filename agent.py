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
from prompts import researcher_prompt

load_dotenv()

os.environ["BYPASS_TOOL_CONSENT"] = "true"
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

model = OpenAIModel(
    client_args={
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
    },
    model_id="deepseek/deepseek-v4-flash-0731",
    params={
        "temperature": 0.7,
        "max_tokens": 2000,
    },
)


@tool
def tavily_search(query: str) -> str:
    "Search the web for current and relevant information"
    result = tavily.search(
        query=query,
        search_depth="basic",  # advanced
        max_results=5,  # fixed: was max_result (typo, silently ignored by Tavily)
    )
    print("SEARCHING WEB..........")
    return result


@tool
def fetch_page(url: str) -> str:
    """
    Fetch web page and extract its readable text
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
        print("FETCHING PAGE...........")
        return text[:6000]  # Set on 5000+ just testing that's why
    except Exception as e:
        logging.error(f"Error fetching Page :{e}")
        raise


status_callback = None

def emit_to_frontend(data):
    if status_callback:
        status_callback(data)

@tool
def update_status(
    message: str,
    stage: str = "working",
    url: str = ""
):
    """
    Send a live progress update to the frontend.

    Args:
        message: Short user-visible description.
        stage: Current stage.
        url: URL currently being searched or read, if applicable.
    """
    emit_to_frontend({
        "type": "agent_status",
        "stage": stage,
        "message": message,
        "url": url or None
    })

    return "Status sent successfully."

 

researcher = Agent(
    model=model,
    system_prompt=researcher_prompt,
    tools=[tavily_search, fetch_page, file_write, file_read, file_editor,update_status],
)


if __name__ == "__main__":
    today = date.today().strftime("%B %d, %Y")
    prompt = "How to become Rich?"
    response = researcher(
        f"Today's date is {today} your task is {prompt}"
    )
    print(response)
