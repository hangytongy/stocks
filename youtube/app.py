import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Google Gemini API key
# Best practice: use environment variables for keys
# export GOOGLE_API_KEY="YOUR_API_KEY"
api_key_value = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key_value)

# Define the API endpoint
@app.route('/summarize', methods=['POST'])
def summarize_video():
    """
    API endpoint to summarize a YouTube video using the Gemini API.
    Expects a JSON payload with a 'youtube_url' key.
    """
    try:
        # Get the JSON data from the request
        data = request.get_json()
        youtube_url = data.get('youtube_url')

        # Validate the URL
        if not youtube_url:
            return jsonify({'error': 'Missing "youtube_url" in request'}), 400
        
        # Ensure the URL is for YouTube
        if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            return jsonify({'error': 'The provided URL is not a valid YouTube link.'}), 400

        # Define the prompt for the Gemini model
        prompt = "Analyze the following YouTube video content. Provide a concise summary and a list of key takeaways. Do not remove any information that could help the user understand the subject matter"

        # Make the API call
        response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=types.Content(
            parts=[
                types.Part(text=prompt),
                types.Part(
                    file_data=types.FileData(file_uri=youtube_url, mime_type="video/mp4")
                )
            ]
        )
    )


        # Return the summary as a JSON response
        return jsonify({'summary': response.text}), 200

    except Exception as e:
        # Handle potential errors during the API call
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
