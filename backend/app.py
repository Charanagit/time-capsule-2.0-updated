from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymongo
import bcrypt
from datetime import datetime, timedelta
from flask_session import Session
import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

# Allowed file types for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Flask app setup
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "timeCaps")

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

# Connect to MongoDB (update MONGO_URI as needed)
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://myUser:MySecurePassword123@cluster1.m2maqcc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database('total_records')
users_collection = db.users
posts_collection = db.posts
scheduled_messages_collection = db.scheduled_messages

# ----------------- Utility Functions -----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------- Routes -----------------
@app.route('/test_db')
def test_db():
    try:
        users_collection.insert_one({"test": "connection_check"})
        users_collection.delete_one({"test": "connection_check"})
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {e}"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        stored_hashed_password = None

        # Try to fetch user from MongoDB if collection is available
        if users_collection is not None:
            try:
                user = users_collection.find_one({"username": username})
                if user and 'password' in user:
                    stored_hashed_password = user['password']
                    if isinstance(stored_hashed_password, str):
                        stored_hashed_password = stored_hashed_password.encode('utf-8')
            except Exception:
                # DB not reachable or some error, fallback to dummy
                stored_hashed_password = None

        # Fallback dummy user
        dummy_user = {
            "username": "demo",
            "password": bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt())
        }

        # Use dummy user if no DB user found or DB failed
        if stored_hashed_password is None and username == dummy_user['username']:
            stored_hashed_password = dummy_user['password']

        # Validate password
        if stored_hashed_password and bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('home'))

        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('signup'))

        if users_collection.find_one({"username": username}):
            flash('Username already exists!')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })

        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        scheduled_messages = scheduled_messages_collection.find({"username": username})
        return render_template('home.html', username=username, scheduled_messages=scheduled_messages)
    flash('Please log in first.')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/delete_scheduled_message/<message_id>', methods=['POST'])
def delete_scheduled_message(message_id):
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    result = scheduled_messages_collection.delete_one({"_id": ObjectId(message_id)})
    flash('Scheduled message deleted successfully.' if result.deleted_count > 0 else 'Failed to delete the scheduled message.')
    return redirect(url_for('view_scheduled_messages'))

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        visibility = request.form['visibility']
        user = session['username']

        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                image_filename = secure_filename(image.filename)
                image.save(os.path.join(UPLOAD_FOLDER, image_filename))

        post_data = {
            "username": user,
            "title": title,
            "content": content,
            "visibility": visibility,
            "image": image_filename,
            "created_at": datetime.utcnow()
        }
        posts_collection.insert_one(post_data)
        flash('Post published successfully!')
        return redirect(url_for('home'))

    return render_template('post.html')

@app.route('/view_posts')
def view_posts():
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    username = session['username']
    user_posts = posts_collection.find({'username': username}).sort('created_at', -1)
    return render_template('view_posts.html', posts=user_posts)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule_message():
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        caption = request.form.get('caption')
        message = request.form.get('messageText')
        visibility = request.form.get('visibility')
        schedule_type = request.form.get('scheduleType')
        custom_date = request.form.get('customDate') if schedule_type == 'custom' else None

        schedule_date = (
            datetime.utcnow() + timedelta(days=365) if schedule_type == 'oneYear'
            else datetime.strptime(custom_date, '%Y-%m-%d') if custom_date
            else datetime.utcnow()
        )

        user = session['username']
        image_attachment = request.files.get('imageAttachment')
        image_url = None

        if image_attachment and allowed_file(image_attachment.filename):
            image_filename = secure_filename(image_attachment.filename)
            image_attachment.save(os.path.join(UPLOAD_FOLDER, image_filename))
            image_url = url_for('static', filename='uploads/' + image_filename)

        scheduled_messages_collection.insert_one({
            "username": user,
            "caption": caption,
            "message": message,
            "schedule_date": schedule_date,
            "visibility": visibility,
            "image_url": image_url,
            "created_at": datetime.utcnow()
        })

        flash('Message scheduled successfully!')
        return redirect(url_for('home'))

    return render_template('schedule.html')

@app.route('/view_scheduled_messages')
def view_scheduled_messages():
    if 'username' not in session:
        flash('Please log in to view your scheduled messages.')
        return redirect(url_for('login'))

    username = session['username']
    scheduled_messages = scheduled_messages_collection.find({"username": username})
    return render_template('view_scheduled_messages.html', scheduled_messages=scheduled_messages)

# ----------------- Main -----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

#TEST GITHUB