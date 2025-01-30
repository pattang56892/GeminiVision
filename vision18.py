import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import json

# Load environment variables
load_dotenv()

# Configure the Gemini (PaLM) model
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

# Dynamically determine our JSON filename based on the script's name
script_name = os.path.splitext(os.path.basename(__file__))[0]  
data_filename = f"{script_name}_data.json"

# Define the path to the image file
image_paths = ["uploads/p30.png", "uploads/p34.png"]

# Attempt to open the images
images = []
for path in image_paths:
    try:
        images.append(Image.open(path))
    except FileNotFoundError:
        print(f"Error: The file '{path}' was not found. Ensure the path is correct.")
        exit(1)

# Initialize the Gemini model
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

def chat_with_model():
    print("Welcome to the Gemini Vision assistant!")
    print(f"Saving conversation data to: {data_filename}")
    print("Ask me to generate something based on the image contents, or type 'exit' to quit.")

    # Load existing conversation data (if any)
    data = {"messages": []}
    try:
        with open(data_filename, "r") as f:
            previous_data = json.load(f)
            data["messages"] = previous_data.get("messages", [])
    except FileNotFoundError:
        # If the file doesn't exist yet, we start with an empty conversation
        pass

    while True:
        user_input = input("\nYour prompt: ")
        if user_input.lower() == "exit":
            print("Exiting the conversation. Goodbye!")
            break

        # Append the user's message to the conversation
        data["messages"].append({"role": "user", "content": user_input})

        try:
            # Generate the response using the user’s prompt + images
            response = model.generate_content([user_input, *images])
            assistant_text = response.text

            print("\nGemini's Response:")
            print(assistant_text)

            # Append Gemini’s response to the conversation
            data["messages"].append({"role": "assistant", "content": assistant_text})

            # Save the updated conversation to data_filename
            with open(data_filename, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error: {e}")
            # Attempt to save the current conversation data even if an error occurs
            with open(data_filename, "w") as f:
                json.dump(data, f, indent=2)

# Entry point
if __name__ == "__main__":
    chat_with_model()