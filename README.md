# Silent Keylogger with AI Analysis

## ⚠️ Educational Purpose Only
This tool is for **educational and research purposes only**. Unauthorized monitoring may be illegal.

## 📦 Components
1. **keylogger_server.py**
   - Flask server (port 5000)
   - Gemini AI analysis
   - Log file generation
   - Pattern matching fallback

2. **keylogger.py**
   - Console mode keylogger
   - Window monitoring
   - Sends data to server

3. **keylogger.pyw** 
   - Silent mode (no console)
   - Background operation
   - Same as keylogger.py

## 🚀 Quick Start
1. Install requirements:
```bash
pip install flask pynput requests google-generativeai pywin32
