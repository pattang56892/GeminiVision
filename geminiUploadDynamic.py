import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    if not os.path.exists(path):
        print(f"Error: The file '{path}' does not exist.")
        return None
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    return files

# Create the model
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Start the chat session by asking for the document name
chat_session = model.start_chat(
    history=[
        {
            "role": "system",
            "parts": [
                {"text": "Please show me the name of the document that you would like to upload."},
            ],
        },
    ]
)

# Get the document name from the user
document_name = input("Enter the document name (including .pdf extension): ")

# Update the file path to reflect the file in your directory
file_path = os.path.join("uploads", document_name)

# Debugging step to verify the file path
print(f"Looking for file at: {file_path}")

# Upload the PDF file
file = upload_to_gemini(file_path, mime_type="application/pdf")
if not file:
    exit("Upload failed. Please check the file path.")

# Wait for the file to be ready
wait_for_files_active([file])

# Continue the chat session by informing the model about the uploaded document
response = chat_session.send_message({
    "role": "user",  # Specify the role here
    "parts": [
        {"text": f"I have uploaded the document '{document_name}'."}
    ]
})

# Print the response (this is to ensure we're getting a response correctly)
print(response)

# Dynamic questioning in a loop
while True:
    user_question = input("Ask a question about the document (or type 'exit' to end): ")
    if user_question.lower() == 'exit':
        break
    
    # Send the user's question to the model
    response = chat_session.send_message({
        "role": "user",  # Specify the role here
        "parts": [
            {"text": user_question}
        ]
    })
    
    # Print the model's response
    print(response.text)
    print(response.usage_metadata)
