import os
import time
import google.generativeai as genai
from IPython.display import display, Markdown
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

# Define the path to the file in the 'Uploads' directory
file_path = os.path.join(os.getcwd(), 'uploads', 'your_image.jpg')

# Upload the file
sample_file = genai.upload_file(path=file_path, display_name="Sample JPG Image")

print(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")

# Set the model to Gemini 1.5 Pro
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# Generate a creative description of the image
response = model.generate_content(["Describe the image with a creative description.", sample_file])

# Display the response using Markdown
print(">" + response.text)

# Display the token usage
token_usage = response.usage_metadata
print("Token Usage:", token_usage)
