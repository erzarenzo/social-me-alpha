import requests

print("\033[92mAI Agent Ready! Type a command or 'exit' to quit.\033[0m")

while True:
    command = input("\033[94mYou:\033[0m ")  # Ask user for a command

    if command.lower() in ["exit", "quit"]:
        print("\033[91mExiting chat.\033[0m")
        break  # Exit the loop if user types 'exit' or 'quit'

    # Send request to FastAPI server
    response = requests.post(
        "http://localhost:8000/execute",
        json={"command": command}
    )

    # Process response
    if response.status_code == 200:
        result = response.json().get("result", "No response")
        print(f"\033[93mAgent:\033[0m {result}")  # Yellow color for response
    else:
        print("\033[91mAgent: Error processing request\033[0m")  # Red for errors
