import os
import json
import re
import base64
import textwrap
from datetime import datetime
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image  # Keep PIL import, might be useful for future image manipulation

# ✅ Handle timezone correctly
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone  # For older Python versions

# Load the .env file from one level up
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(env_path)

# ✅ Configure Gemini model
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-pro-exp")

# ✅ Ensure Eastern Time (New York / Toronto)
EASTERN_TIME = ZoneInfo("America/New_York") if "ZoneInfo" in globals() else timezone("America/New_York")

# ✅ Dynamically determine JSON filename
script_name = os.path.splitext(os.path.basename(__file__))[0]
data_filename = f"{script_name}_data.json"

# ✅ Generate a session ID for tracking
session_id = f"session_{datetime.now(EASTERN_TIME).strftime('%Y%m%d_%H%M%S')}"

# ✅ Function to load images as Base64 (Improved Version)
def load_image_as_base64(image_path: str) -> Optional[dict]:
    """Reads an image file and converts it to Base64 format, handling errors.
    Returns a dictionary with MIME type and data, or None on failure.
    """
    if not os.path.exists(image_path):
        print(f"⚠️ Warning: The file '{image_path}' was not found. Skipping.")
        return None

    try:
        with open(image_path, "rb") as img_file:
            data = base64.b64encode(img_file.read()).decode("utf-8")
        # Use a dictionary for MIME types (more maintainable)
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",  # Handle both .jpg and .jpeg
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = mime_types.get(ext)  # Use .get() for safety

        if mime_type is None:
            print(f"⚠️ Warning: Unsupported image format for {image_path}")
            return None  # Or raise an exception if it's a critical error

        return {"mime_type": mime_type, "data": data}

    except Exception as e:
        print(f"❌ Error loading image '{image_path}': {e}")
        return None

# --- Main image loading logic ---
# Define three upload folders with their respective filename ranges and formats
upload_folders = [
    ("uploads01", range(1, 20), "p{num:02d}.png"),   # p01.png to p19.png
    ("uploads02", range(21, 30), "p{num:03d}.png"),   # p021.png to p029.png
    ("uploads03", range(31, 40), "p{num:03d}.png"),   # p031.png to p039.png
]

# Load images from all folders using the specified filename format
images = []
for folder, num_range, fmt in upload_folders:
    for num in num_range:
        filename = fmt.format(num=num)
        full_path = os.path.join(folder, filename)
        img = load_image_as_base64(full_path)
        if img is not None:
            images.append(img)

# ✅ Generate response from image & text with error handling (Improved Version)
def generate_response(prompt: str) -> Optional[str]:
    contents = images + [prompt]  # Concatenate the list of image dicts with the prompt
    try:
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        print(f"❌ Error processing your request: {e}")
        return None  # Or handle the error as appropriate

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
        messages.insert(0, assistant_message)  # Insert assistant message at index 0
        messages.insert(0, user_message)         # Insert user message at index 0
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
