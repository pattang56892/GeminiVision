import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

# Define the paths to the image files
image_paths = ["uploads/p03.png", "uploads/p04.png", "uploads/p05.png", "uploads/p06.png", "uploads/p07.png", "uploads/p08.png", "uploads/p09.png", "uploads/p10.png"]  # Add paths to multiple images

# Open the images using PIL and store them in a list
images = []
for path in image_paths:
    try:
        images.append(Image.open(path))
    except FileNotFoundError:
        print(f"Error: The file '{path}' was not found. Ensure the path is correct.")
        exit(1)

# Choose a Gemini model
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# Function to handle conversation prompts
def chat_with_model():
    print("Welcome to the Gemini Vision assistant!")
    print("Ask me to generate something based on the image contents, or type 'exit' to quit.")

    while True:
        user_input = input("\nYour prompt: ")
        if user_input.lower() == "exit":
            print("Exiting the conversation. Goodbye!")
            break
        
        try:
            # Generate content using the prompt and all images
            response = model.generate_content([user_input, *images])
            print("\nGemini's Response:")
            print(response.text)
        except Exception as e:
            print(f"Error: {e}")

# Start the chat
if __name__ == "__main__":
    chat_with_model()
