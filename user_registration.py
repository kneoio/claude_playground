#user_registration.py
import json

import anthropic
from dotenv import load_dotenv
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_BASE_URL = os.getenv('API_BASE_URL')
APP_NAME = os.getenv('APP_NAME')
JWT_TOKEN = os.getenv('JWT_TOKEN')

USER_CHECK_ENDPOINT = f"{API_BASE_URL}/api/{APP_NAME}/owners/telegram"
USER_REGISTRATION_ENDPOINT = f"{API_BASE_URL}/api/{APP_NAME}/owners/telegram/"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_tool_definitions(directory):
    tools = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                tools.append(json.load(file))
    return tools

tools = load_tool_definitions('tools')

def process_tool_call(tool_name, tool_input):
    headers = {
        'Authorization': f'Bearer {JWT_TOKEN}',
        'Content-Type': 'application/json'
    }

    if tool_name == "check_user":
        url = f"{USER_CHECK_ENDPOINT}/{tool_input['telegramName']}"
        logger.info(f"Sending GET request to: {url}")
        logger.info(f"Request payload: {json.dumps(tool_input, indent=2)}")
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        if response.status_code == 200:
            try:
                return json.dumps(response.json(), indent=2)
            except requests.exceptions.JSONDecodeError:
                return f"Received non-JSON response: {response.text}"
        elif response.status_code == 404:
            return "User does not exist"
        else:
            return f"Error: {response.status_code}, Response: {response.text}"
    elif tool_name == "register_user":
        payload = {"telegramName": tool_input['telegramName']}
        logger.info(f"Sending POST request to: {USER_REGISTRATION_ENDPOINT}")
        logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
        response = requests.post(USER_REGISTRATION_ENDPOINT, json=payload, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        if response.status_code == 200:
            try:
                return json.dumps(response.json(), indent=2)
            except requests.exceptions.JSONDecodeError:
                return f"Received non-JSON response: {response.text}"
        else:
            return f"Error: {response.status_code}, Response: {response.text}"

user_name = input("Enter the telegram name to check: ")

messages = [
    {"role": "user", "content": f"Check if user with telegram name '{user_name}' exists and register if not."}
]

while True:
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=messages,
        tools=tools
    )

    if response.stop_reason == "tool_use":
        tool_use = response.content[-1]
        tool_name = tool_use.name
        tool_input = tool_use.input

        logger.info(f"Tool use: {tool_name}")
        logger.info(f"Tool input: {tool_input}")

        tool_result = process_tool_call(tool_name, tool_input)

        logger.info(f"Tool result: {tool_result}")

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(tool_result)
            }]
        })
    else:
        print(response.content[0].text)
        break