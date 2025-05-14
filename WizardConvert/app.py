import os
import logging
import time
from flask import Flask, render_template, request, jsonify, send_file, session
from utils.converter import convert_video, validate_youtube_url
import tempfile
import uuid
import shutil

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "wizard_secret_key")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a temporary directory to store conversions
# Use a persistent, non-temporary directory to avoid temp files being deleted too quickly
temp_dir = os.path.join(os.getcwd(), 'temp_downloads')
os.makedirs(temp_dir, exist_ok=True)

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """API endpoint to convert YouTube videos to MP3/MP4"""
    try:
        # Get input from request
        youtube_url = request.form.get('youtube_url')
        format_type = request.form.get('format')
        
        # Validate inputs
        if not youtube_url:
            return jsonify({'status': 'error', 'message': 'No YouTube URL provided'}), 400
        
        if format_type not in ['mp3', 'mp4']:
            return jsonify({'status': 'error', 'message': 'Invalid format. Choose either mp3 or mp4'}), 400
        
        # Validate YouTube URL
        if not validate_youtube_url(youtube_url):
            return jsonify({'status': 'error', 'message': 'Invalid YouTube URL'}), 400
        
        # Generate a unique ID for this conversion
        conversion_id = str(uuid.uuid4())
        output_path = os.path.join(temp_dir, conversion_id)
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Check if cookies file was uploaded
        cookies_path = None
        if 'cookies_file' in request.files:
            cookies_file = request.files['cookies_file']
            
            if cookies_file and cookies_file.filename.endswith('.txt'):
                # Save cookies file to the temporary directory
                cookies_path = os.path.join(output_path, 'cookies.txt')
                cookies_file.save(cookies_path)
                logger.info("Cookies file uploaded and saved")
        
        # Start conversion process
        result = convert_video(youtube_url, format_type, output_path, cookies_path)
        
        if result['status'] == 'success':
            # Store the file path in session for later download
            session[conversion_id] = result['file_path']
            
            # Return success with necessary information
            return jsonify({
                'status': 'success',
                'message': 'Conversion successful!',
                'conversion_id': conversion_id,
                'title': result['title']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during conversion: {error_msg}")
        
        # Provide more user-friendly error messages
        if "Sign in to confirm you're not a bot" in error_msg or "YouTube bot protection triggered" in error_msg:
            if "even with cookies" in error_msg:
                message = "YouTube bot protection detected even with cookies. Your cookies may be invalid or expired."
            elif "Try uploading your YouTube cookies file" in error_msg:
                message = "YouTube bot protection detected. Try uploading your YouTube cookies file or use a different video."
            else:
                message = "YouTube bot protection detected. Try uploading your YouTube cookies file, use a different video, or try again later."
        elif "Video unavailable" in error_msg:
            message = "This video is unavailable or restricted. Try a different video."
        elif "private video" in error_msg.lower():
            message = "This video is private and cannot be accessed."
        elif "copyright" in error_msg.lower():
            message = "This video cannot be downloaded due to copyright restrictions."
        elif "ffmpeg" in error_msg.lower():
            message = "Error during media conversion. Please try a different video."
        elif "'NoneType' object" in error_msg or "not subscriptable" in error_msg:
            message = "Failed to process video information. YouTube may be restricting access to this video."
        elif "cookies" in error_msg.lower():
            message = "Error with cookies file. Make sure it's in the correct format (Netscape/Mozilla)."
        else:
            message = f"An error occurred: {error_msg}"
            
        return jsonify({'status': 'error', 'message': message}), 500

@app.route('/download/<conversion_id>', methods=['GET'])
def download(conversion_id):
    """Download the converted file"""
    try:
        # Get the file path from session
        file_path = session.get(conversion_id)
        logger.debug(f"Session file path for {conversion_id}: {file_path}")
        
        # If file path is not in session or doesn't exist, try to find it in the temp directory
        if not file_path or not os.path.exists(file_path):
            # Try to locate the file in the temporary directory
            conversion_dir = os.path.join(temp_dir, conversion_id)
            if os.path.exists(conversion_dir):
                # Look for any mp3 or mp4 file in the directory
                for file in os.listdir(conversion_dir):
                    if file.endswith('.mp3') or file.endswith('.mp4'):
                        file_path = os.path.join(conversion_dir, file)
                        # Update session with the found file path
                        session[conversion_id] = file_path
                        logger.debug(f"Found file at: {file_path}")
                        break
            
            # If still no file found, return error
            if not file_path or not os.path.exists(file_path):
                logger.error(f"File not found for conversion_id: {conversion_id}")
                return jsonify({'status': 'error', 'message': 'File not found or expired'}), 404
        
        # Get filename from path
        filename = os.path.basename(file_path)
        logger.debug(f"Sending file: {filename}")
        
        # Send the file to the client
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during download: {error_msg}")
        
        # Provide more user-friendly error messages
        if "No such file" in error_msg:
            message = "The file you're trying to download was not found. Please try converting again."
        else:
            message = f"Error downloading the file: {error_msg}. Please try again."
            
        return jsonify({'status': 'error', 'message': message}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# We're not cleaning up the temp_downloads directory automatically anymore
# to prevent files from being removed before download.
# Instead, we'll implement a function to clean up old files periodically

def cleanup_old_files():
    """Remove files older than 1 hour"""
    try:
        current_time = time.time()
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            # If it's been more than 1 hour since the file was created
            if os.path.isdir(item_path) and os.path.getmtime(item_path) < current_time - 3600:
                shutil.rmtree(item_path)
                logger.info(f"Removed old conversion directory: {item_path}")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")

# Schedule the cleanup to run periodically (every hour)
import threading
def run_cleanup_periodically():
    """Run cleanup every hour"""
    cleanup_old_files()
    # Schedule next run in 1 hour
    cleanup_timer = threading.Timer(3600, run_cleanup_periodically)
    cleanup_timer.daemon = True
    cleanup_timer.start()

# Start the cleanup scheduler
run_cleanup_periodically()
