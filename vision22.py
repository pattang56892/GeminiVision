import os
import json
import re
import base64
import textwrap
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image


# ✅ Handle timezone correctly
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone  # For older Python versions

# ✅ Load environment variables
load_dotenv()

# ✅ Configure Gemini model
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-exp")  

# ✅ Ensure Eastern Time (New York / Toronto)
EASTERN_TIME = ZoneInfo("America/New_York") if "ZoneInfo" in globals() else timezone("America/New_York")

# ✅ Dynamically determine JSON filename
script_name = os.path.splitext(os.path.basename(__file__))[0]
data_filename = f"{script_name}_data.json"

# ✅ Generate a session ID for tracking
session_id = f"session_{datetime.now(EASTERN_TIME).strftime('%Y%m%d_%H%M%S')}"

# ✅ Paths to local images
image_paths = ["uploads/p43.png"]

# ✅ Function to load images as Base64
def load_image_as_base64(image_path):
    """Reads an image file and converts it to Base64 format."""
    if not os.path.exists(image_path):
        print(f"⚠️ Warning: The file '{image_path}' was not found. Skipping it.")
        return None

    try:
        with open(image_path, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type = "image/png"

            if image_path.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"

            return {"mime_type": mime_type, "data": base64_str}

    except Exception as e:
        print(f"❌ Error loading image '{image_path}': {e}")
        return None

# ✅ Attempt to load images
images = [img for path in image_paths if (img := load_image_as_base64(path))]

# ✅ Generate response from image & text with error handling
def generate_response(prompt):
    contents = images + [prompt]

    try:
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        print(f"❌ Error processing your request: {e}")
        return None  # Prevent saving error messages as valid responses

# ✅ Load existing conversation history
def load_existing_conversation(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                return existing_data.get("messages", [])
        except json.JSONDecodeError:
            return []
    return []

# ✅ Append messages incrementally (instead of overwriting)
def save_messages_incrementally(file_path, user_message, assistant_message):
    messages = load_existing_conversation(file_path)

    # ✅ Add only valid messages
    if assistant_message["content"]:
        # Prepend new messages
        messages.insert(0, assistant_message) # Insert assistant message at index 0
        messages.insert(0, user_message)      # Insert user message at index 0
        try:
           with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"messages": messages}, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"❌ Error writing to JSON file: {e}")

# ✅ Convert conversation data into readable text format
def format_conversation_to_text(input_path, output_path, max_width=80, indent_size=4):
    try:
        with open(input_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            messages = data.get('messages', [])

        output_lines = []
        indent = " " * indent_size
        for msg in messages:
            timestamp = msg.get('timestamp', 'Unknown Time')
            role = msg.get('role', 'Unknown')
            content = msg.get('content', 'No Content')

            if role == 'user':
                role_label = 'User'
            elif role == 'assistant':
                role_label = 'Assistant'
            else:
                role_label = f"Unknown role {role}"

            # Split the content into lines, handle multiline content
            content_lines = content.splitlines()
            
            formatted_lines = []
            for line in content_lines:
                # Wrap each line individually.
                wrapped_line = textwrap.fill(line, width=max_width - indent_size)
                formatted_lines.extend([f"{indent}{wrapped_line_part}" for wrapped_line_part in wrapped_line.splitlines()])
            
            output_lines.append(f"[{timestamp}] {role_label}:")
            output_lines.extend(formatted_lines)

            # Add an extra blank line after the content if it contained blank lines
            if any(not line.strip() for line in content_lines):
                 output_lines.append("")
            output_lines.append("")

        with open(output_path, 'w', encoding="utf-8") as f:
            f.write('\n'.join(output_lines))

        print(f"📄 Formatted conversation saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error formatting conversation: {e}")

# ✅ Main Chat Function
def chat_with_model():
    print("🔹 Welcome to the Gemini Vision Assistant!")
    print(f"💾 Storing conversation in: {data_filename}")

    messages = load_existing_conversation(data_filename)

    while True:
        prompt = input("Your prompt: ").strip()
        if prompt.lower() == "exit":
            print("👋 Exiting chat. Goodbye!")
            break
        if not prompt:
            continue  # Skip empty input

        # ✅ Create timestamped user message
        timestamp = datetime.now(EASTERN_TIME).isoformat()
        user_message = {
            "session_id": session_id,
            "timestamp": timestamp,
            "role": "user",
            "content": prompt
        }
        messages.append(user_message)

        # ✅ Generate response from Gemini
        response_text = generate_response(prompt)

        if response_text is None:
            print("⚠️ No valid response received. Skipping message storage.")
            continue  # Skip saving the response if it's an error

        # ✅ Create timestamped assistant response
        assistant_message = {
            "session_id": session_id,
            "timestamp": datetime.now(EASTERN_TIME).isoformat(),
            "role": "assistant",
            "content": response_text
        }
        messages.append(assistant_message)

        # ✅ Save conversation incrementally
        save_messages_incrementally(data_filename, user_message, assistant_message)

        # ✅ Save formatted output
        format_conversation_to_text(data_filename, f"{script_name}_formatted_data.txt")

        print("\n🤖 **Gemini's response:**\n")
        print(response_text)
        print("—" * 40)

# ✅ Run the chat session
if __name__ == "__main__":
    chat_with_model()
