import os
from dotenv import load_dotenv
import certifi

# Fix SSL certificate verification issues
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Load environment variables from .env file
load_dotenv()

# Use environment variables for API keys
os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.callbacks import StdOutCallbackHandler
from langchain_core.callbacks import CallbackManager
from langchain.agents import create_react_agent
import time
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from visit_webpage import WebpageVisitor
from functions.gaia import get_gaia_attachment
from functions.reverse import reverse_word
from functions.youtube import youtube_info

# API key for OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Define the REACT system template that explicitly instructs tool usage
REACT_SYSTEM_TEMPLATE = """You are a helpful assistant that has access to the following tools:

{tools}

To use the tools, you MUST follow this format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the tool
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: [your response here]

Begin! Remember give short, precise answers and to always use the exact format above, including the 'Thought:', 'Action:', 'Action Input:', 'Observation:', and 'Final Answer:' prefixes.
"""

# Initialize the LLM with OpenRouter
llm = ChatOpenAI(
    # model="deepseek/deepseek-chat-v3-0324:free",
    model="qwen/qwen-2.5-72b-instruct:free",
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0
)

# Initialize the search tool
search_tool = DuckDuckGoSearchRun()

search = GoogleSearchAPIWrapper()

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Initialize the webpage visitor
webpage_visitor = WebpageVisitor()

# Create a LangChain Tool
tools = [
    Tool(
        name="search",
        description="Search Google for recent results.",
        func=search.run,
    ),
    Tool(name="web_search",
         func=search_tool.run,
         description="Search Web for recent results."
    ),
    Tool(
        name="wikipedia",
        func=wikipedia.run,
        description="Search Wikipedia for information on a topic. Useful for detailed background information on historical events, people, places, or concepts. Input should be a search query."
    ),
    Tool(
        name="youtube_video_info",
        func=youtube_info,
        description="Gets transcriptions from a YouTube video. Input should be a YouTube video URL."
    ),
    # Tool(
    #     name="visit_webpage",
    #     func=webpage_visitor.forward,
    #     description="Visit a webpage and extract its content. Input should be a valid URL starting with http:// or https://."
    # ),
    Tool(
        name="reverse_text",
        func=reverse_word,
        description="Reverses the characters in a word or text. Input should be a text string you want to reverse."
    ),
    Tool(
        name="get_gaia_attachment",
        func=get_gaia_attachment,
        description="Retrieves an attachment from the GAIA benchmark dataset using its ID/hash."
    )
]

class BasicAgent:
    def __init__(self):
        print("BasicAgent initialized.")

    def __call__(self, question: str, taskId: str) -> str:
        print(f"Agent received question (first 50 chars): {question[:50]}...")

        # Create a prompt template with explicit instructions to use tools
        prompt = ChatPromptTemplate.from_messages([
            ("system", REACT_SYSTEM_TEMPLATE),
            ("human", "Input: {input} Task ID: {task_id}"),
            ("ai", "{agent_scratchpad}")
        ])

        # Create a ReAct agent instead of functions agent
        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        # Set up callback handler for detailed logging
        handler = StdOutCallbackHandler()
        callback_manager = CallbackManager([handler])

        # Create the agent executor with callbacks
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,  # Reduced to match the system prompt
            callbacks=[handler],
            max_iterations=3,  # Increased max iterations to match the system prompt
            return_intermediate_steps=True  # Return the intermediate steps for post-processing
        )

        try:
            # Run the agent with properly formatted input
            start_time = time.time()
            response = agent_executor.invoke({"input": question, "chat_history": [], "task_id": taskId})
            execution_time = time.time() - start_time
            print(f"Agent execution completed in {execution_time:.2f} seconds for task {taskId}.")

            # Extract just the final answer from the output
            output = response["output"]
            print(f"Final answer: {output}")
            return output
            
        except Exception as e:
            print(f"Error during agent execution: {str(e)}")
            return f"I apologize, but I encountered an issue while processing your request. Please try asking in a different way or with more specific information."
