import os

# Get the base directory of this folder to make the database path absolute
basedir = os.path.abspath(os.path.dirname(__file__))

class config:
    # 1. Secret Key for Sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_for_quizmaster_123'
    
    # 2. Database path (using absolute path prevents errors on different OS)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'quizmaster.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 3. Add your Gemini Key here so app.py can find it
    GEMINI_API_KEY = "AIzaSyAd_R9Aoe16XDPVZzuK2WGLiO0CEFUx28YY"