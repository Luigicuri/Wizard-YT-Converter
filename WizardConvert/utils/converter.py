import os
import re
import logging
import json
import subprocess
from urllib.parse import urlparse, parse_qs
import yt_dlp

# Configure logging
logger = logging.getLogger(__name__)

def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube URL
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    youtube_regex_match = re.match(youtube_regex, url)
    
    if youtube_regex_match:
        return True
    
    # Check for YouTube shortened URLs
    if 'youtu.be' in url:
        parsed_url = urlparse(url)
        if parsed_url.netloc == 'youtu.be' and len(parsed_url.path) > 1:
            return True
    
    return False

def get_video_info(youtube_url, cookies_path=None):
    """
    Get video title and info using yt-dlp
    
    Args:
        youtube_url (str): YouTube video URL
        cookies_path (str, optional): Path to cookies file
        
    Returns:
        dict: Video information
    """
    try:
        # Configure options to help bypass bot detection
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'geo_bypass': True,  # Try to bypass geo restrictions
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Use mobile player API
            'socket_timeout': 30,
            'force_generic_extractor': False,
            'sleep_interval': 5,  # Add some delay between requests
            'max_sleep_interval': 10,
            # Add random user agent to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # Add cookies file if provided
        if cookies_path and os.path.exists(cookies_path):
            logger.info(f"Using cookies file: {cookies_path}")
            ydl_opts['cookiefile'] = cookies_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        
        # Check if info is None (which would happen if extraction failed)
        if info is None:
            raise Exception("Failed to retrieve video information. YouTube may be restricting access.")
            
        # Get sanitized title for filename
        video_title = "".join([c for c in info['title'] if c.isalnum() or c in ' -_.']).strip()
        return {'title': video_title, 'id': info['id']}
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error getting video info: {error_str}")
        
        # Check if it's related to bot detection
        if "Sign in to confirm you're not a bot" in error_str:
            if cookies_path:
                raise Exception("YouTube bot protection triggered even with cookies. Your cookies may be invalid or expired.")
            else:
                raise Exception("YouTube bot protection triggered. Try uploading your YouTube cookies file or try a different video.")
        elif "'NoneType' object" in error_str or "not subscriptable" in error_str:
            raise Exception("Failed to process video information. YouTube may be restricting access to this video.")

def convert_video(youtube_url, format_type, output_path, cookies_path=None):
    """
    Convert YouTube video to MP3 or MP4 using yt-dlp
    
    Args:
        youtube_url (str): YouTube video URL
        format_type (str): Output format (mp3 or mp4)
        output_path (str): Path to save the converted file
        cookies_path (str, optional): Path to cookies file
        
    Returns:
        dict: Status of the conversion operation
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Get video info
        video_info = get_video_info(youtube_url, cookies_path)
        if video_info is None:
            return {
                'status': 'error',
                'message': 'Failed to retrieve video information. YouTube may be restricting access.'
            }
        video_title = video_info['title']
        
        # Set the filename
        if format_type == 'mp3':
            filename = f"{video_title}.mp3"
            output_file = os.path.join(output_path, filename)
            
            # Configure yt-dlp options for audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_file,
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'geo_bypass': True,  # Try to bypass geo restrictions
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Use mobile player API
                'socket_timeout': 30,
                'force_generic_extractor': False,
                'sleep_interval': 3,  # Add some delay between requests
                'max_sleep_interval': 5,
                # Add random user agent to avoid bot detection
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            # Add cookies file if provided
            if cookies_path and os.path.exists(cookies_path):
                logger.info(f"Using cookies file for conversion: {cookies_path}")
                ydl_opts['cookiefile'] = cookies_path
        elif format_type == 'mp4':
            filename = f"{video_title}.mp4"
            output_file = os.path.join(output_path, filename)
            
            # Configure yt-dlp options for video
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_file,
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'geo_bypass': True,  # Try to bypass geo restrictions
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Use mobile player API
                'socket_timeout': 30,
                'force_generic_extractor': False,
                'sleep_interval': 3,  # Add some delay between requests
                'max_sleep_interval': 5,
                # Add random user agent to avoid bot detection
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'merge_output_format': 'mp4',
            }
            
            # Add cookies file if provided
            if cookies_path and os.path.exists(cookies_path):
                logger.info(f"Using cookies file for conversion: {cookies_path}")
                ydl_opts['cookiefile'] = cookies_path
        
        # Download the file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # The exact output path may have been modified by yt-dlp to avoid duplicates
        # Let's find the actual file
        for file in os.listdir(output_path):
            file_path = os.path.join(output_path, file)
            if os.path.isfile(file_path) and (file.endswith(f".{format_type}")):
                # This is our downloaded file
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'title': video_title
                }
        
        # If we didn't find the file, something went wrong
        raise Exception("File was not created after download")
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error converting video: {error_str}")
        
        # Provide more specific error messages
        if "Sign in to confirm you're not a bot" in error_str:
            if cookies_path:
                message = "YouTube bot protection triggered even with cookies. Your cookies may be invalid or expired."
            else:
                message = "YouTube bot protection triggered. Try uploading your YouTube cookies file or try a different video."
        elif "This video is private" in error_str:
            message = "This video is private and cannot be accessed."
        elif "Video unavailable" in error_str:
            message = "This video is unavailable. It may have been removed or is restricted."
        elif "copyright" in error_str.lower():
            message = "This video cannot be downloaded due to copyright restrictions."
        elif "age-restricted" in error_str.lower():
            message = "This video is age-restricted and cannot be downloaded."
        elif "'NoneType' object" in error_str or "not subscriptable" in error_str:
            message = "Failed to process video information. YouTube may be restricting access to this video."
        elif "cookies" in error_str.lower():
            message = "Error with cookies file. Make sure it's in the correct format (Netscape/Mozilla)."
        else:
            message = f"Error converting video: {error_str}"
        
        return {
            'status': 'error',
            'message': message
        }
