from crewai import Agent
from langchain.agents import Tool

def create_agents(tools):
    task_manager = Agent(
        role="Task Manager",
        goal="Interpret user requests and determine appropriate actions",
        backstory=(
            "You are an AI assistant that understands natural language requests "
            "and converts them into actionable tasks using available tools."
        ),
        tools=tools,
        verbose=True
    )
    
    executor = Agent(
        role="Task Executor",
        goal="Execute tasks using the provided tools",
        backstory=(
            "You are an efficient executor that specializes in using tools "
            "to complete tasks as instructed."
        ),
        tools=tools,
        verbose=True
    )
    
    return task_manager, executor