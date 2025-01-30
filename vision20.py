#!/usr/bin/env python3
import os
import json
import re
import base64
import textwrap
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Handle timezone correctly
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone      # For older Python versions

# Load environment variables
load_dotenv()

# Configure Gemini model
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Ensure Eastern Time (New York / Toronto)
if "ZoneInfo" in globals():
    EASTERN_TIME = ZoneInfo("America/New_York")
else:
    EASTERN_TIME = timezone("America/New_York")

# Dynamically determine JSON filename
script_name = os.path.splitext(os.path.basename(__file__))[0]
data_filename = f"{script_name}_data.json"

# Generate a session ID for tracking
session_id = "session_" + datetime.now(EASTERN_TIME).strftime("%Y%m%d_%H%M%S")

# Paths to local images
image_paths = ["uploads/p38.png", "uploads/p39.png", "uploads/p40.png"]

def load_image_as_base64(image_path):
    """
    Reads an image file and converts it to Base64 format.
    Returns a dict containing 'mime_type' and 'data' keys, or None on failure.
    """
    if not os.path.exists(image_path):
        print(f"⚠️ Warning: The file '{image_path}' was not found. Skipping it.")
        return None

    try:
        with open(image_path, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type = "image/png"

            lower_path = image_path.lower()
            if lower_path.endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif lower_path.endswith(".gif"):
                mime_type = "image/gif"
            elif lower_path.endswith(".webp"):
                mime_type = "image/webp"

            return {"mime_type": mime_type, "data": base64_str}
    except Exception as e:
        print(f"❌ Error loading image '{image_path}': {e}")
        return None

# Attempt to load images
images = [img for path in image_paths if (img := load_image_as_base64(path))]

def generate_response(prompt):
    """
    Sends a prompt (plus any loaded images) to the Gemini model,
    returns the model's text response or None on error.
    """
    contents = images + [prompt]

    try:
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        print(f"❌ Error processing your request: {e}")
        return None  # Prevent saving error messages as valid responses

def load_existing_conversation(file_path):
    """
    Loads an existing conversation from JSON.
    Returns the 'messages' array or an empty list if file doesn't exist/parse.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                return existing_data.get("messages", [])
        except json.JSONDecodeError:
            return []
    return []

def save_messages_incrementally(file_path, user_message, assistant_message):
    """
    Appends user and assistant messages to the conversation, saves to JSON.
    Only saves if the assistant_message['content'] is valid (not None/empty).
    """
    messages = load_existing_conversation(file_path)
    if assistant_message["content"]:
        messages.append(user_message)
        messages.append(assistant_message)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"messages": messages}, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"❌ Error writing to JSON file: {e}")

def format_conversation_to_text(input_path, output_path):
    """
    Puts timestamp and role on separate lines and writes a more readable
    text file at 'output_path'. Adds blank lines between messages.
    
    Example final format for each message:
      [2025-01-30T07:20:30]
      User:
      Hello there, how are you?
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            messages = data.get("messages", [])

        output_lines = []

        for msg in messages:
            timestamp = msg.get("timestamp", "Unknown Time")
            role = msg.get("role", "Unknown Role")
            content = msg.get("content", "(No Content)")

            # Decide the label
            if role == "user":
                role_label = "User:"
            elif role == "assistant":
                role_label = "Assistant:"
            else:
                role_label = f"Unknown({role}):"

            # Line 1: Timestamp
            output_lines.append(f"[{timestamp}]")
            # Line 2: Role label
            output_lines.append(role_label)

            # Wrap the content so it doesn't overflow horizontally
            wrapped_lines = textwrap.wrap(content, width=100)
            if wrapped_lines:
                output_lines.extend(wrapped_lines)
            else:
                output_lines.append("(No content)")

            # Blank line after each message block
            output_lines.append("")

        # Write the resulting lines to the text file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))

        print(f"Formatted conversation saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error formatting conversation: {e}")

def chat_with_model():
    """
    Main chat loop. Prompts user for input, calls Gemini for responses,
    saves conversation incrementally, and writes out a formatted text file.
    Ends when user types 'exit'.
    """
    print("🔹 Welcome to the Gemini Vision Assistant!")
    print(f"💾 Storing conversation in: {data_filename}\n")

    messages = load_existing_conversation(data_filename)

    while True:
        prompt = input("Your prompt: ").strip()
        if prompt.lower() == "exit":
            print("👋 Exiting chat. Goodbye!")
            break

        if not prompt:
            continue  # Skip empty input

        # Timestamped user message
        timestamp = datetime.now(EASTERN_TIME).isoformat()
        user_message = {
            "session_id": session_id,
            "timestamp": timestamp,
            "role": "user",
            "content": prompt
        }
        messages.append(user_message)

        # Generate assistant response
        response_text = generate_response(prompt)
        if response_text is None:
            print("⚠️ No valid response received. Skipping message storage.")
            continue

        # Timestamped assistant message
        assistant_message = {
            "session_id": session_id,
            "timestamp": datetime.now(EASTERN_TIME).isoformat(),
            "role": "assistant",
            "content": response_text
        }
        messages.append(assistant_message)

        # Save JSON conversation incrementally
        save_messages_incrementally(data_filename, user_message, assistant_message)

        # Produce a nicely formatted text file
        formatted_file = f"{script_name}_formatted_data.txt"
        format_conversation_to_text(data_filename, formatted_file)

        # Print the assistant's raw response in console
        print("\n🤖 **Gemini's response:**\n")
        print(response_text)
        print("—" * 40)

if __name__ == "__main__":
    chat_with_model()
