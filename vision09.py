import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

# Define the path to the image file
image_path = "uploads/p16.png"  # Use the p01.png file from the uploads directory

# Open the image using PIL
try:
    sample_image = Image.open(image_path)
except FileNotFoundError:
    print(f"Error: The file '{image_path}' was not found. Ensure the path is correct.")
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
            # Generate content using the image and user input
            response = model.generate_content([user_input, sample_image])
            print("\nGemini's Response:")
            print(response.text)
        except Exception as e:
            print(f"Error: {e}")

# Start the chat
if __name__ == "__main__":
    chat_with_model()
