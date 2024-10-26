from flask import Flask, render_template, request, jsonify
import logging  # Import the standard logging module
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
from pytube import YouTube
import re
import sys
import traceback

app = Flask(__name__)

# Configure logging correctly
app.logger.setLevel(logging.DEBUG)  # Now using the correct logging.DEBUG
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Load environment variables with error handling
load_dotenv()
GEMINI_API_KEY = "AIzaSyAMYpivJ4uwYaQdbPoRCPy-qXqAf0G8w1A"
if not GEMINI_API_KEY:
    app.logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY is required")

# Configure Gemini with error handling
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
except Exception as e:
    app.logger.error(f"Failed to configure Gemini API: {str(e)}")
    raise

def extract_video_id(url):
    """Extract YouTube video ID with improved error handling"""
    app.logger.debug(f"Extracting video ID from URL: {url}")
    try:
        if not url:
            raise ValueError("Empty URL provided")
            
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                app.logger.debug(f"Successfully extracted video ID: {video_id}")
                return video_id
                
        raise ValueError("Invalid YouTube URL format")
    except Exception as e:
        app.logger.error(f"Error extracting video ID: {str(e)}")
        return None

def get_video_transcript(video_id):
    """Get video transcript with improved error handling"""
    app.logger.debug(f"Fetching transcript for video ID: {video_id}")
    try:
        if not video_id:
            raise ValueError("No video ID provided")
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        if not transcript:
            raise ValueError("Empty transcript received")
            
        full_transcript = " ".join([entry['text'] for entry in transcript])
        app.logger.debug(f"Successfully retrieved transcript of length: {len(full_transcript)}")
        return full_transcript
    except Exception as e:
        app.logger.error(f"Transcript error for video {video_id}: {str(e)}")
        return None

@app.route('/summarize', methods=['POST'])
def summarize():
    """Enhanced summarize endpoint with comprehensive error handling"""
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data received")
            
        url = data.get('url', '').strip()
        if not url:
            raise ValueError("No URL provided")
            
        app.logger.info(f"Processing summary request for URL: {url}")
        
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract valid video ID")
            
        transcript = get_video_transcript(video_id)
        if not transcript:
            raise ValueError("Could not retrieve video transcript")
            
        # Limit transcript length and create prompt
        prompt = f"""
        Create an engaging and informative summary of this YouTube video content:
        {transcript[:4000]}
        Structure the summary as follows:
        1. Overview
        - What is this video about?
        - Main message or purpose
         
        2. Key Highlights
        - Important points discussed
        - Notable examples or demonstrations
        - Interesting facts presented
         
        3. Main Takeaways
        - Core lessons or insights
        - Valuable tips shared
        - Important conclusions
         
        4. Audience Value
        - What viewers will learn
        - How they can apply this information
        - Who would benefit most
        """
        
        app.logger.debug("Generating summary with Gemini")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API")
            
        app.logger.info("Successfully generated summary")
        return jsonify({
            'status': 'success',
            'summary': response.text
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        app.logger.error(f"Error in summarize endpoint: {str(e)}\n{error_details}")
        return jsonify({
            'status': 'error',
            'message': 'Video processing failed. Please verify the URL and try again.',
            'error': str(e)
        }), 400

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
