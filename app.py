from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
from pytube import YouTube
import re

app = Flask(__name__)

# Load environment variables
load_dotenv()
#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY="AIzaSyAMYpivJ4uwYaQdbPoRCPy-qXqAf0G8w1A"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

def extract_video_id(url):
    try:
        if 'youtu.be' in url:
            return url.split('/')[-1]
        if 'youtube.com' in url:
            return url.split('v=')[1].split('&')[0]
    except:
        return None

def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"Transcript error: {str(e)}")
        return None

def get_video_details(url):
    try:
        yt = YouTube(url)
        return {
            'title': yt.title,
            'author': yt.author,
            'thumbnail': yt.thumbnail_url,
            'views': format_views(yt.views),
            'length': format_duration(yt.length),
            'description': yt.description[:200] + '...' if yt.description else ''
        }
    except:
        video_id = extract_video_id(url)
        return {
            'title': 'Video Title',
            'author': 'Content Creator',
            'thumbnail': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            'views': '0',
            'length': '0:00',
            'description': ''
        }

def format_views(views):
    if views >= 1000000:
        return f"{views/1000000:.1f}M views"
    elif views >= 1000:
        return f"{views/1000:.1f}K views"
    return f"{views} views"

def format_duration(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"
@app.route('/summarize', methods=['POST'])
def summarize():
   try:
       data = request.get_json()
       url = data.get('url', '').strip()
       video_id = extract_video_id(url)
       transcript = get_video_transcript(video_id)

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

       Make the summary clear, concise, and easy to understand while capturing the essence of the video content.
       """

       response = model.generate_content(prompt)
        
       return jsonify({
           'status': 'success',
           'summary': response.text
       })

   except Exception as e:
       print(f"Error details: {str(e)}")
       return jsonify({
           'status': 'error',
           'message': 'Processing failed. Please try again.'
       })
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
