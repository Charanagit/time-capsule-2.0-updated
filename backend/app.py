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
UPLOAD_FOLDER = 'static/uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__, template_folder='/app/templates', static_folder='/app/static')

app.secret_key = "timeCaps"  # Secret key for session and flashing messages

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/total_records")
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database('total_records')
users_collection = db.users
posts_collection = db.posts
scheduled_messages_collection = db.scheduled_messages



@app.route('/test_db')
def test_db():
    try:
        users_collection.insert_one({"test": "connection_check"})  # Insert dummy data
        users_collection.delete_one({"test": "connection_check"})  # Remove it after testing
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {e}"


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"Login attempt: {username}")  # Debugging step

        user = users_collection.find_one({"username": username})

        if user:
            print(f"User found in DB: {user}")  # Debugging step
        else:
            print("User not found in DB")

        if user and 'password' in user:
            stored_hashed_password = user['password']
            print(f"Stored hashed password (from DB): {stored_hashed_password}")  # Debugging step
            
            if isinstance(stored_hashed_password, str):  
                stored_hashed_password = stored_hashed_password.encode('utf-8')

            try:
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                    session['username'] = username
                    flash('Login successful!')
                    print("Login successful! Redirecting to home...")
                    return redirect(url_for('home'))
                else:
                    print("Password does not match")
            except ValueError as e:
                print(f"Error during bcrypt check: {e}")
        else:
            print("User object invalid or missing password")

        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')


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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('Username')
        email = request.form.get('email')
        password = request.form.get('password')
        if users_collection.find_one({"username": username}):
            flash('Username already exists!')
            return redirect(url_for('signup'))
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({"username": username, "email": email, "password": hashed_password})
        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/delete_scheduled_message/<message_id>', methods=['POST'])
def delete_scheduled_message(message_id):
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))
    result = scheduled_messages_collection.delete_one({"_id": ObjectId(message_id)})
    flash('Scheduled message deleted successfully.' if result.deleted_count > 0 else 'Failed to delete the scheduled message.')
    return redirect(url_for('view_scheduled_messages'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        schedule_date = datetime.utcnow() + timedelta(days=365) if schedule_type == 'oneYear' else datetime.strptime(custom_date, '%Y-%m-%d') if custom_date else datetime.utcnow()
        user = session['username']
        image_attachment = request.files.get('imageAttachment')
        image_url = None
        if image_attachment and allowed_file(image_attachment.filename):
            image_filename = secure_filename(image_attachment.filename)
            image_attachment.save(os.path.join(UPLOAD_FOLDER, image_filename))
            image_url = f"static/uploads/{image_filename}"
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



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)



