from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import shlex
import openai  # Make sure you have `pip install openai`
import os

app = FastAPI()

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("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")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Set OPENAI_API_KEY as an environment variable.")

openai.api_key = OPENAI_API_KEY

# Define a request model for structured JSON input
class CommandRequest(BaseModel):
    command: str

def convert_natural_to_shell(natural_command: str) -> str:
    """Uses OpenAI to convert a natural language request into a shell command."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # Use GPT-4 Turbo or another model
            messages=[
                {"role": "system", "content": "You are an AI that converts natural language to Linux shell commands."},
                {"role": "user", "content": f"Convert this request to a Linux shell command: {natural_command}"}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

@app.post("/execute")
def execute_command(request: CommandRequest):
    """Executes a shell command after converting natural language if necessary."""
    command = convert_natural_to_shell(request.command)

    if command.startswith("ERROR"):
        return {"command": request.command, "result": command}

    try:
        # Securely split command into arguments
        cmd_parts = shlex.split(command)
        # Execute the command
        result = subprocess.run(cmd_parts, capture_output=True, text=True)
        # Get the output (stdout or stderr)
        output = result.stdout.strip() if result.stdout else result.stderr.strip()

        return {"command": command, "result": output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
