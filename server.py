"""
Flask web server to keep the bot alive on Render's free tier.
This allows external services to ping the bot and prevent it from spinning down.
"""

from flask import Flask
from threading import Thread
import os

app = Flask(__name__)


@app.route('/')
def home():
    """Health check endpoint."""
    return "WFRP Traveling Bot is alive! 🚢"


@app.route('/health')
def health():
    """Health check endpoint for monitoring services."""
    return {"status": "healthy", "bot": "WFRP Traveling Bot"}


def run():
    """Run the Flask server."""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    """Start the Flask server in a separate thread."""
    server = Thread(target=run)
    server.daemon = True
    server.start()
