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
prompt_ = '''Act as an expert analyst for a major financial institution. Your task is to provide two separate, world-class summaries of a YouTube interview transcript. These summaries are intended for Michael Platt, the head of Bluecrest Capital Management, and his CTO, Jeffrey.

**Michael Platt's Summary**

* Focus on the economic reality, not on hype.
* Highlight verifiable macro implications of the work. Avoid speculation.
* Include specific numbers, statistics, and their sources.

**Jeffrey's Summary**

* Focus on academically defensible positions and their justifications.
* Provide key details, logic, and business builds.
* Analyze the technological capabilities, including enhancements or degradations.

Your response must be a single output containing both summaries. Start with Platt's summary first, followed by Jeffrey's summary. Do not omit any key information, and ensure the summaries are as long as necessary to fully address the needs of both individuals.
'''

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
        prompt = prompt_

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
