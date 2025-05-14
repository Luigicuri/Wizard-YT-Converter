/**
 * WizardConvert - YouTube to MP3/MP4 Converter
 * Main JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const conversionForm = document.getElementById('conversion-form');
    const youtubeUrlInput = document.getElementById('youtube-url');
    const convertBtn = document.getElementById('convert-btn');
    const conversionStatus = document.getElementById('conversion-status');
    const progressBar = document.querySelector('.progress-bar');
    const statusText = document.querySelector('.status-text');
    const successAlert = document.getElementById('success-alert');
    const successMessage = document.getElementById('success-message');
    const errorAlert = document.getElementById('error-alert');
    const errorMessage = document.getElementById('error-message');
    const downloadSection = document.getElementById('download-section');
    const videoTitle = document.getElementById('video-title');
    const downloadBtn = document.getElementById('download-btn');
    const urlError = document.getElementById('url-error');

    // Conversion ID to track the current conversion
    let currentConversionId = null;

    // Form submission
    conversionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset previous states
        resetUI();
        
        // Get form data
        const youtubeUrl = youtubeUrlInput.value.trim();
        const formatType = document.querySelector('input[name="format"]:checked').value;
        
        // Validate YouTube URL
        if (!validateYouTubeUrl(youtubeUrl)) {
            youtubeUrlInput.classList.add('is-invalid');
            urlError.textContent = 'Please enter a valid YouTube URL';
            return;
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('youtube_url', youtubeUrl);
        formData.append('format', formatType);
        
        // Add cookies file if provided
        const cookiesFile = document.getElementById('cookies-file').files[0];
        if (cookiesFile) {
            formData.append('cookies_file', cookiesFile);
        }
        
        // Start conversion
        startConversion(formData);
    });
    
    // YouTube URL validator
    function validateYouTubeUrl(url) {
        // More specific regex to validate YouTube URLs
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})(\S*)?$/;
        return youtubeRegex.test(url);
    }
    
    // Start conversion process
    function startConversion(formData) {
        // Show conversion status and disable form
        conversionStatus.classList.remove('d-none');
        convertBtn.disabled = true;
        youtubeUrlInput.disabled = true;
        document.querySelectorAll('input[name="format"]').forEach(input => {
            input.disabled = true;
        });
        
        // Start progress animation
        simulateProgress();
        
        // Send conversion request to server
        fetch('/convert', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Stop progress animation
            progressBar.style.width = '100%';
            
            if (data.status === 'success') {
                // Store conversion ID for download
                currentConversionId = data.conversion_id;
                
                // Update status message
                statusText.textContent = 'Conversion completed successfully!';
                
                // Show success message
                successAlert.classList.remove('d-none');
                successMessage.textContent = 'Your file is ready for download.';
                
                // Prepare download section
                videoTitle.textContent = data.title;
                downloadSection.classList.remove('d-none');
                
                // Wait a bit for UI to process changes
                setTimeout(() => {
                    conversionStatus.classList.add('d-none');
                    enableForm();
                }, 1500);
            } else {
                // Handle error
                handleConversionError(data.message);
            }
        })
        .catch(error => {
            // Handle network or other errors
            handleConversionError('Network error or server issue. Please try again.');
            console.error('Error:', error);
        });
    }
    
    // Handle conversion errors
    function handleConversionError(message) {
        // Update UI for error state
        progressBar.style.width = '0%';
        conversionStatus.classList.add('d-none');
        
        // Show error message
        errorAlert.classList.remove('d-none');
        errorMessage.textContent = message || 'An unknown error occurred.';
        
        // Re-enable form
        enableForm();
    }
    
    // Simulate progress for better UX
    function simulateProgress() {
        let width = 0;
        let intervalTime = 180; // Start with faster updates
        
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
                return;
            }
            
            // Increase progress with variable speed to simulate realistic conversion
            if (width < 20) {
                width += 4; // Fast at start (metadata fetching)
                intervalTime = 150;
            } else if (width < 40) {
                width += 3; // Medium speed (video analysis)
                intervalTime = 200;
            } else if (width < 60) {
                width += 2; // Slower (downloading)
                intervalTime = 300;
            } else if (width < 80) {
                width += 0.8; // Very slow (conversion processing)
                intervalTime = 400;
            } else {
                width += 0.5; // Final touches
                intervalTime = 500;
            }
            
            progressBar.style.width = width + '%';
            
            // Update status text based on progress
            if (width < 20) {
                statusText.textContent = 'Fetching video information...';
            } else if (width < 40) {
                statusText.textContent = 'Preparing the magic cauldron...';
            } else if (width < 60) {
                statusText.textContent = 'Extracting audio/video content...';
            } else if (width < 80) {
                statusText.textContent = 'Brewing your file format...';
            } else {
                statusText.textContent = 'Finalizing your magic potion...';
            }
        }, intervalTime);
    }
    
    // Download button event listener
    downloadBtn.addEventListener('click', function() {
        if (currentConversionId) {
            // Create a temporary link and simulate click
            window.location.href = `/download/${currentConversionId}`;
        }
    });
    
    // Enable form inputs after conversion
    function enableForm() {
        convertBtn.disabled = false;
        youtubeUrlInput.disabled = false;
        document.querySelectorAll('input[name="format"]').forEach(input => {
            input.disabled = false;
        });
    }
    
    // Reset UI to initial state
    function resetUI() {
        // Hide all alerts and status elements
        conversionStatus.classList.add('d-none');
        successAlert.classList.add('d-none');
        errorAlert.classList.add('d-none');
        downloadSection.classList.add('d-none');
        
        // Reset progress bar
        progressBar.style.width = '0%';
        
        // Clear validation errors
        youtubeUrlInput.classList.remove('is-invalid');
        urlError.textContent = '';
        
        // Reset conversion ID
        currentConversionId = null;
    }
    
    // Add input event listener to clear validation errors when typing
    youtubeUrlInput.addEventListener('input', function() {
        if (this.classList.contains('is-invalid')) {
            this.classList.remove('is-invalid');
            urlError.textContent = '';
        }
    });
});
