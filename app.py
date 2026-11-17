"""
CareerLens — Application Root WSGI Entry Point
==============================================
Enables standard zero-configuration deployment on platforms like Render,
Railway, Fly.io, Heroku, and Hugging Face Spaces.

Run locally:
    python app.py

Run in production:
    gunicorn app:app
"""

import os
from backend.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\nCareerLens server running on port {port}")
    print(f"URL -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
