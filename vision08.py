import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_1_5_API_KEY"))

# Define the directory containing the images
image_folder = "uploads/CurrentStateOfReasoningWithLLMs"  # Updated folder path
output_folder = "outputs/CurrentStateOfReasoningWithLLMs"  # Folder to save processed images

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all .png files in the directory
image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]

if not image_files:
    print(f"No .png files found in '{image_folder}'")
    exit(1)

# Choose a Gemini model
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# Define the output log file
output_log_path = os.path.join(output_folder, "output.txt")

# Function to process each image
def process_images():
    with open(output_log_path, "w") as log_file:
        print("Welcome to the Gemini Vision assistant!", file=log_file)
        print(f"Processing all .png images from '{image_folder}'...\n", file=log_file)

        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)

            try:
                # Open the image using PIL
                sample_image = Image.open(image_path)
                print(f"Processing '{image_file}'...", file=log_file)
                
                # Generate content using the image
                response = model.generate_content(["Describe this image:", sample_image])
                
                # Display the response
                print(f"Gemini's Response for '{image_file}':", file=log_file)
                print(response.text, file=log_file)
                print("\n", file=log_file)

                # Optionally save or process further
                sample_image.save(os.path.join(output_folder, image_file))

            except FileNotFoundError:
                print(f"Error: The file '{image_path}' was not found. Skipping.", file=log_file)
            except Exception as e:
                print(f"Error processing '{image_file}': {e}", file=log_file)

# Start the image processing
if __name__ == "__main__":
    process_images()
