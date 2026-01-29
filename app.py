# app.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
from io import BytesIO
from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename 
from google.generativeai.types import HarmCategory, HarmBlockThreshold 

# --- App Configuration ---
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# --- Database Path Fix ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- File Upload Config ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

# --- Database Setup ---
from database import db, User, History  
db.init_app(app)                       

login_manager = LoginManager(app)
login_manager.login_view = 'login' 

# --- AI Configuration ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

# --- UPDATED SYSTEM PROMPT (SMART FILTERING) ---
SYSTEM_PROMPT = """
You are a specialized assistant for skin lesion analysis.

STEP 1: IMAGE VALIDATION
First, look at the image. Does it appear to be human skin, a skin lesion, a rash, or a dermatological condition?

- IF NO (e.g., it is a car, animal, plant, building, face without lesions, or random object):
  Output EXACTLY this message and stop:
  "⚠️ content_warning: The uploaded image does not appear to be a skin lesion. This tool is designed specifically for skin analysis. Please upload a valid image."

- IF YES (it is skin):
  Proceed to STEP 2.

STEP 2: DESCRIPTIVE ANALYSIS
Provide a visual description following these strict rules:
1. Describe what you see in neutral, objective terms (color, shape, texture, borders).
2. Use bullet points.
3. Do NOT provide a diagnosis (e.g., do not say "This is melanoma").
4. Do NOT give medical advice.
5. At the end, add this exact line:
   "Disclaimer: This is a descriptive analysis and not a medical diagnosis. Please consult a qualified dermatologist for confirmation."
"""
# --- END OF UPDATE ---

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Page Routes ---
@app.route('/')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']

        if User.query.filter_by(username=username).first():
            return "User already exists. <a href='/'>Login</a>"

        new_user = User(username=username, age=int(age))
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/app')
@login_required
def index():
    user_name = current_user.username
    return render_template('index.html', name=user_name)

@app.route('/history')
@login_required
def history_page():
    return render_template('history.html', name=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- API Routes ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({"success": True, "message": "Login successful"})
    
    return jsonify({"success": False, "message": "Invalid username or password"})


@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        filename = secure_filename(file.filename)
        user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{current_user.id}")
        os.makedirs(user_upload_dir, exist_ok=True)
        
        image_save_path = os.path.join(user_upload_dir, filename)
        file.save(image_save_path)
        
        image_db_path = f"uploads/user_{current_user.id}/{filename}"
        
        file.stream.seek(0)
        image = PIL.Image.open(file.stream)

        # --- SAFETY SETTINGS ---
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model = genai.GenerativeModel('models/gemini-2.5-flash') 
        response = model.generate_content(
            [SYSTEM_PROMPT, image],
            safety_settings=safety_settings
        )
        
        new_history = History(
            user_id=current_user.id,
            image_path=image_db_path, 
            analysis=response.text
        )
        db.session.add(new_history)
        db.session.commit()
        
        return jsonify({"analysis": response.text})

    except Exception as e:
        return jsonify({"error": f"An analysis error occurred: {str(e)}"}), 500

@app.route('/api/history')
@login_required
def get_history():
    history_items = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()
    history_list = [
        {
            "id": item.id,
            "image_path": item.image_path,
            "analysis": item.analysis,
            "date": item.timestamp.strftime('%Y-%m-%d %H:%M')
        } for item in history_items
    ]
    return jsonify(history_list)

@app.route('/api/history/delete/<int:item_id>', methods=['DELETE'])
@login_required
def delete_history_item(item_id):
    item = History.query.get(item_id)
    
    if not item or item.user_id != current_user.id:
        return jsonify({"success": False, "message": "Item not found or unauthorized"}), 404
        
    try:
        image_full_path = os.path.join('static', item.image_path)
        if os.path.exists(image_full_path):
            os.remove(image_full_path)
            
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({"success": True, "message": "History item deleted"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.cli.command("create-db")
def create_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    app.run(debug=True)