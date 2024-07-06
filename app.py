from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import requests
import tweepy
from tavily import TavilyClient
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Use an environment variable for the secret key

# Print statements to debug environment variable loading
print("FLASK_SECRET_KEY:", os.getenv('FLASK_SECRET_KEY'))
print("TAVILY_API_KEY:", os.getenv('TAVILY_API_KEY'))
print("GEMINI_API_KEY:", os.getenv('GEMINI_API_KEY'))
print("TWITTER_API_KEY:", os.getenv('TWITTER_API_KEY'))
print("TWITTER_API_KEY_SECRET:", os.getenv('TWITTER_API_KEY_SECRET'))
print("TWITTER_ACCESS_TOKEN:", os.getenv('TWITTER_ACCESS_TOKEN'))
print("TWITTER_ACCESS_TOKEN_SECRET:", os.getenv('TWITTER_ACCESS_TOKEN_SECRET'))
print("TWITTER_BEARER_TOKEN:", os.getenv('TWITTER_BEARER_TOKEN'))

# Configuration with provided API keys
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_KEY_SECRET = os.getenv('TWITTER_API_KEY_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Configure Tavily Client
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# Configure Google generative AI
genai.configure(api_key=GEMINI_API_KEY)

# Create the model with generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Authenticate to Twitter using tweepy.Client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_KEY_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

def generate_tweet(query, context=None):
    if not context:
        # Perform the search query with Tavily
        try:
            response = tavily.search(query=query, search_depth="advanced")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return str(e), None
        except Exception as e:
            print(f"Other error occurred: {e}")
            return str(e), None

        # Extract and format the search results as context
        context = " ".join([obj["content"] for obj in response.get('results', [])])
    
    # Define the prompt for the generative AI model
    prompt = f"""You are an engagement master! Craft a concise and informative tweet summarizing the situation: {context}. 
    Use your wit to spark conversation and evoke a positive emotional response from your audience. 
    Include a call to action to keep them interacting. Top it off with trending hashtags to expand your reach! 
    Make sure you make a tweet in 100 characters!
    {context}"""

    # Start the chat session
    chat_session = model.start_chat(history=[])
    # Send the prompt to the model
    response = chat_session.send_message(prompt)
    
    return response.text, context

@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if username == 'venu' and password == 'Archana@03':
            session['authenticated'] = True
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/generate_tweet', methods=['POST'])
def generate_tweet_route():
    if not session.get('authenticated'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json()
    query = data.get('query')
    context = data.get('context')
    tweet, context = generate_tweet(query, context)
    return jsonify({'tweet': tweet, 'context': context})

@app.route('/post_tweet', methods=['POST'])
def post_tweet():
    if not session.get('authenticated'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json()
    message = data.get('tweet')
    try:
        client.create_tweet(text=message)
        return jsonify({'status': 'success', 'message': 'Tweet posted successfully!'})
    except tweepy.TweepyException as e:
        return jsonify({'status': 'error', 'message': str(e)})

