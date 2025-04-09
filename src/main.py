import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Crew, Agent, Task
from langchain_groq import ChatGroq
from langchain.agents import Tool
import traceback
import time # Import time for delays
from datetime import datetime, timedelta # Import datetime utilities

# --- Pydantic Models (Keep as before) ---
class TaskOutputModel(BaseModel):
    tool: str = Field(description="The name of the tool to use ('slack_notify' or 'create_calendar_event').")
    parameters: Dict[str, Any] = Field(description="The dictionary of parameters for the chosen tool.")

class SlackNotifyInput(BaseModel):
    channel: str = Field(description="The Slack channel name (e.g., '#general').")
    message: str = Field(description="The message text to send.")

class CreateCalendarEventInput(BaseModel):
    summary: str = Field(description="The title or summary of the calendar event.")
    start_time: str = Field(description="The start date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")
    end_time: str = Field(description="The end date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")
    description: Optional[str] = Field(default=None, description="An optional description for the event.")

# --- LLM Initialization (Keep as before) ---
try:
    llm = ChatGroq(
        temperature=0.7,
        model_name="groq/llama3-8b-8192",
        groq_api_key=os.getenv('GROQ_API_KEY')
    )
except Exception as e:
    print(f"Error initializing LLM: {e}")
    exit(1)


# --- Tool Functions (Keep simulated versions or uncomment your actuals) ---
def run_slack_notify(channel: str, message: str) -> str:
    print(f"--- Running Slack: Send '{message}' to {channel} ---")
    # Add your actual Slack logic here if needed
    return f"Successfully sent message to {channel}"

def run_create_calendar_event(summary: str, start_time: str, end_time: str, description: Optional[str] = None) -> str:
    print(f"--- Running Calendar: Create '{summary}' from {start_time} to {end_time} (Desc: {description}) ---")
    # Add your actual Calendar logic here if needed
    return f"Successfully created calendar event: '{summary}'"

# --- Tool Initialization (Keep as before) ---
try:
    slack_tool = Tool( name="slack_notify", func=run_slack_notify, description="Send a message to a specified Slack channel.", args_schema=SlackNotifyInput )
    calendar_tool = Tool( name="create_calendar_event", func=run_create_calendar_event, description="Create an event on the primary Google Calendar using ISO 8601 format times (e.g., '2025-04-10T14:00:00Z').", args_schema=CreateCalendarEventInput )
    tools = [slack_tool, calendar_tool]
except Exception as e:
     print(f"Error initializing tools: {e}")
     exit(1)

# --- Agent Creation (Keep as before, verbose=False) ---
task_manager = Agent(
    role="Task Manager",
    goal="Interpret user requests, identify the correct tool (slack_notify or create_calendar_event) and extract ALL necessary parameters based on the tool's input schema.",
    # Added context about current date to backstory
    backstory="You are an AI assistant that translates natural language into structured tool calls. Accurately extract parameters like 'channel', 'message', 'summary', 'start_time', 'end_time'. Dates/times MUST be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Assume a 1-hour duration if not specified. Pay close attention to relative dates provided in the context.",
    tools=tools,
    llm=llm,
    verbose=False
)

executor = Agent(
    role="Task Executor",
    goal="Execute tasks by calling the specified tool with the exact parameters provided by the Task Manager.",
    backstory="You receive the tool name and parameters and execute the corresponding tool function, reporting the result.",
    tools=tools,
    llm=llm,
    verbose=False
)

# --- Task Processing Function (with Retry and Date Context) ---
def process_request(user_input: str) -> str:
    """Process user input through the agent crew with retry logic"""
    max_retries = 2
    retry_delay_seconds = 7 # Base delay, increase if needed

    # --- Add Date Context ---
    now = datetime.now()
    # Ensure timezone awareness for Z format (UTC). Use timezone naive for calculation then format.
    # Or use a timezone library if you need local time converted precisely.
    # For simplicity, let's calculate naive and format as Z (assuming times are meant as UTC or the LLM handles it based on Z)
    tomorrow_dt = now + timedelta(days=1)
    current_date_str = now.strftime('%Y-%m-%d')
    tomorrow_date_str = tomorrow_dt.strftime('%Y-%m-%d')
    # ---

    for attempt in range(max_retries + 1):
        try:
            # --- Define Tasks (Inject Date Context) ---
            interpret_task = Task(
                # Inject current date and calculated tomorrow's date into the description
                description=(
                    f"Current date is {current_date_str}. Tomorrow's date is {tomorrow_date_str}. "
                    f"Interpret this request: '{user_input}'. Determine the correct tool and extract its parameters precisely "
                    f"according to the tool's input schema. Ensure date/time values are in ISO 8601 format "
                    f"(YYYY-MM-DDTHH:MM:SSZ, using the provided dates) and assume a 1-hour duration if end time isn't specified."
                ),
                agent=task_manager,
                expected_output=(
                    "A JSON object strictly conforming to the TaskOutputModel schema, containing 'tool' name and 'parameters' "
                    "dictionary matching the chosen tool's args_schema (SlackNotifyInput or CreateCalendarEventInput). "
                    "Use the provided dates for 'today' or 'tomorrow'."
                ),
                output_json=TaskOutputModel
            )

            execute_task = Task(
                description="Execute the tool call determined by the Task Manager.",
                agent=executor,
                expected_output="The result from executing the tool (e.g., 'Successfully sent message...' or 'Successfully created calendar event...').",
                context=[interpret_task]
            )
            # --- End Task Definition ---

            crew = Crew(
                agents=[task_manager, executor],
                tasks=[interpret_task, execute_task],
                verbose=False
            )

            print(f"\n>>> Kicking off crew (Attempt {attempt + 1}/{max_retries + 1}) for request: '{user_input}'")
            result = crew.kickoff()
            print(f"<<< Crew finished (Attempt {attempt + 1}).")

            # Ensure result is a string
            if isinstance(result, (dict, list)):
                 return json.dumps(result, indent=2)
            else:
                 return str(result) if result is not None else "Crew returned None" # Handle None result

        # Catch specific RateLimitError from LiteLLM
        except Exception as e:
            # Check if the exception is a RateLimitError (might be nested)
            is_rate_limit = False
            original_exception = e
            while original_exception:
                 # Check by type name as direct import might be complex
                 if type(original_exception).__name__ == 'RateLimitError' and 'litellm' in str(type(original_exception)):
                     is_rate_limit = True
                     break
                 # Check common wrappers
                 if hasattr(original_exception, '__cause__') and original_exception.__cause__:
                      original_exception = original_exception.__cause__
                 elif hasattr(original_exception, '__context__') and original_exception.__context__:
                      original_exception = original_exception.__context__
                 else:
                      break # Stop if no further cause/context

            if is_rate_limit and attempt < max_retries:
                print(f"--- Rate Limit Error encountered. Waiting {retry_delay_seconds} seconds before retrying (Attempt {attempt + 1})... ---")
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 1.5 # Optional: exponential backoff
                continue # Go to the next attempt
            else:
                # If it's not a rate limit error or retries are exhausted
                print("--- ERROR TRACEBACK ---")
                print(traceback.format_exc())
                print("--- END ERROR TRACEBACK ---")
                error_type = type(e).__name__
                # Try to extract the specific rate limit message if it was the cause
                if is_rate_limit:
                    error_type = "RateLimitError (Retries Exhausted)"
                return f"Error processing request after {attempt + 1} attempts: {error_type} - {str(e)}"

    # This part should ideally not be reached if max_retries > 0
    return "Error: Max retries exceeded without success."


# --- Main Execution Loop (Keep as before) ---
if __name__ == "__main__":
    required_vars = ['GROQ_API_KEY']
    # Add SLACK_TOKEN back if using actual Slack tool
    # required_vars = ['GROQ_API_KEY', 'SLACK_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set them with:")
        print("export VARIABLE_NAME='your-value'  # Linux/Mac")
        print("set VARIABLE_NAME=your-value      # Windows CMD")
        print("$env:VARIABLE_NAME='your-value' # Windows PowerShell")
        exit(1)

    print("AI Agent (using Groq with retry) is ready. Type your request or 'quit' to exit.")

    try:
        while True:
            try:
                request = input("\nEnter your request: ").strip()
                if request.lower() in ('quit', 'exit'):
                    break
                if not request:
                    continue

                response = process_request(request)
                print("\nResponse:", response)
            except KeyboardInterrupt:
                print("\nUse 'quit' or 'exit' to end the session.")
                continue
            except Exception as e:
                 print(f"\nAn unexpected error occurred in the main loop: {e}")
                 print(traceback.format_exc())

    finally:
        print("\nSession ended. Goodbye!")