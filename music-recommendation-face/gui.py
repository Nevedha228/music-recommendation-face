import os
import random
import webbrowser
import cv2
import numpy as np
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk  # Canvas for game
from dotenv import load_dotenv

# Suppress TensorFlow warnings
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

# DeepFace for emotion detection
from deepface import DeepFace

# Spotify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ----------------------------
# App Config
# ----------------------------
load_dotenv()

emotion_to_genre = {
    "happy": "pop",
    "sad": "acoustic",
    "neutral": "classical",
    "angry": "rock",
    "surprise": "electronic",
    "fear": "ambient",
    "disgust": "alternative"
}

tips = {
    "happy": [
        "Happiness is contagious. Spread it around!",
        "Enjoy the little things in life.",
        "Keep smiling!"
    ],
    "sad": [
        "It's okay to feel sad sometimes. Take time to heal.",
        "Reach out to someone you trust.",
        "Self-care is important."
    ],
    "neutral": [
        "Every moment is a fresh beginning.",
        "Neutral days are perfect for self-reflection.",
        "Stay grounded."
    ],
    "angry": [
        "Breathe deeply. Let go of what you can't control.",
        "Take a break and clear your mind.",
        "Express your feelings constructively."
    ],
    "surprise": [
        "Unexpected moments can lead to beautiful memories.",
        "Embrace the surprises in life.",
        "Adaptability is strength."
    ],
    "fear": [
        "You’re stronger than you think.",
        "Small steps still move you forward.",
        "Talk to someone you trust."
    ],
    "disgust": [
        "Shift focus to something uplifting.",
        "A short walk can reset your mood.",
        "Jot down what’s bothering you, then release it."
    ]
}

# ----------------------------
# Spotify Setup
# ----------------------------
def make_spotify_client():
    try:
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing",
                open_browser=False,
            )
        )
    except Exception as e:
        print(f"[Spotify Auth Warning] {e}")
        return None

sp = make_spotify_client()

# ----------------------------
# Helpers
# ----------------------------
def show_tip(emotion: str):
    if emotion and emotion.lower() in tips:
        messagebox.showinfo(f"Tip for {emotion.capitalize()}", random.choice(tips[emotion.lower()]))
    else:
        messagebox.showinfo("No Tip", "No tips available for the detected emotion.")

def recommend_and_open_song(emotion: str, parent: ctk.CTk):
    if not sp:
        messagebox.showerror("Spotify Not Ready", "Spotify is not authorized properly.")
        return

    genre = emotion_to_genre.get(emotion.lower())
    if not genre:
        messagebox.showinfo("No Genre", f"No genre mapped for emotion: {emotion}")
        return

    try:
        results = sp.search(q=f'genre:"{genre}"', type="track", limit=8)
        items = results.get("tracks", {}).get("items", [])
    except Exception as e:
        messagebox.showerror("Spotify Error", f"Failed to fetch tracks: {e}")
        return

    if not items:
        messagebox.showinfo("No Tracks", "No songs found on Spotify.")
        return

    win = ctk.CTkToplevel(parent)
    win.title("Song Recommendations")
    win.geometry("520x400")

    ctk.CTkLabel(win, text=f"Detected Emotion: {emotion.capitalize()}", font=("Helvetica", 16)).pack(pady=10)

    frame = ctk.CTkScrollableFrame(win, width=480, height=300)
    frame.pack(pady=10, padx=10, fill="both", expand=True)

    def play(url):
        webbrowser.open(url)
        win.destroy()

    for track in items:
        name = track.get("name", "Unknown")
        artists = ", ".join(a["name"] for a in track.get("artists", [])) or "Unknown Artist"
        url = track.get("external_urls", {}).get("spotify")
        if not url:
            continue
        ctk.CTkButton(frame, text=f"{name} — {artists}", command=lambda u=url: play(u)).pack(pady=6, padx=8, fill="x")

def detect_emotion(parent: ctk.CTk):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Could not open camera.")
        return

    messagebox.showinfo("Info", "Camera started. Press 'q' to stop.")
    detected = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

            if isinstance(analysis, list) and analysis:
                dom = analysis[0].get('dominant_emotion')
            elif isinstance(analysis, dict):
                dom = analysis.get('dominant_emotion')
            else:
                dom = None

            if dom:
                detected = dom
                cv2.putText(frame, f'Emotion: {dom}', (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        except Exception as e:
            print(f"[DeepFace] {e}")

        cv2.imshow("Emotion Detection - Press 'q' to stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if detected:
        if messagebox.askyesno("Emotion Detected",
                               f"Detected emotion: {detected.capitalize()}\n\nOpen song recommendations?"):
            recommend_and_open_song(detected, parent)
        show_tip(detected)
    else:
        messagebox.showinfo("No Emotion", "No dominant emotion detected.")

def chatbot_response(user_input: str) -> str:
    responses = {
        "hello": "Hi there! How can I help you today?",
        "hi": "Hello! How are you feeling today?",
        "how are you": "I'm doing great! How about you?",
        "bye": "Goodbye! Have a wonderful day!",
        "recommend a song": "Sure! Click 'Start Camera' and I’ll recommend music based on your mood."
    }
    return responses.get(user_input.strip().lower(), "I'm sorry, I didn't understand that.")

def open_chatbot(parent: ctk.CTk):
    win = ctk.CTkToplevel(parent)
    win.title("Chatbot")
    win.geometry("520x420")

    chat = ctk.CTkTextbox(win, width=480, height=300)
    chat.pack(padx=10, pady=10)

    entry_frame = ctk.CTkFrame(win)
    entry_frame.pack(fill="x", padx=10, pady=10)

    entry = ctk.CTkEntry(entry_frame)
    entry.pack(side="left", fill="x", expand=True, padx=5)

    def send():
        msg = entry.get()
        if msg.strip():
            chat.insert("end", f"You: {msg}\n")
            chat.insert("end", f"Bot: {chatbot_response(msg)}\n")
            chat.see("end")
            entry.delete(0, "end")

    ctk.CTkButton(entry_frame, text="Send", command=send).pack(side="left", padx=5)


class BubbleGame:
    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Bubble Pop Game")
        self.win.geometry("640x520")

        self.canvas = tk.Canvas(self.win, width=600, height=400, bg='lightblue', highlightthickness=0)
        self.canvas.pack(pady=10)

        info_frame = ctk.CTkFrame(self.win)
        info_frame.pack(fill="x", padx=10, pady=5)

        self.score = 0
        self.lives = 5
        self.bubbles = []
        self.update_job = None
        self.spawn_job = None

        self.score_label = ctk.CTkLabel(info_frame, text=f"Score: {self.score}")
        self.score_label.pack(side="left", padx=10)

        self.lives_label = ctk.CTkLabel(info_frame, text=f"Lives: {self.lives}")
        self.lives_label.pack(side="left", padx=10)

        ctk.CTkButton(info_frame, text="Restart", command=self.restart_game).pack(side="right", padx=10)

        self.canvas.bind("<Button-1>", self.check_collision)
        self.restart_game()

        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.cancel_timers()
        self.win.destroy()

    def cancel_timers(self):
        if self.update_job:
            self.win.after_cancel(self.update_job)
            self.update_job = None
        if self.spawn_job:
            self.win.after_cancel(self.spawn_job)
            self.spawn_job = None

    def restart_game(self):
        self.cancel_timers()
        self.score = 0
        self.lives = 5
        self.score_label.configure(text=f"Score: {self.score}")
        self.lives_label.configure(text=f"Lives: {self.lives}")
        self.canvas.delete("all")
        self.bubbles.clear()
        self.spawn_bubble()
        self.schedule_update()

    def spawn_bubble(self):
        x = random.randint(50, 550)
        y = 400
        radius = random.randint(20, 40)
        bubble = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill='blue', outline="")
        self.bubbles.append((bubble, radius))
        self.spawn_job = self.win.after(1000, self.spawn_bubble)

    def schedule_update(self):
        self.update_game()
        self.update_job = self.win.after(50, self.schedule_update)

    def update_game(self):
        for bubble, radius in list(self.bubbles):
            self.canvas.move(bubble, 0, -5)
            x1, y1, x2, y2 = self.canvas.coords(bubble)
            if y2 < 0:
                self.canvas.delete(bubble)
                self.bubbles.remove((bubble, radius))
                self.lives -= 1
                self.lives_label.configure(text=f"Lives: {self.lives}")
                if self.lives <= 0:
                    self.game_over()
                    return

    def check_collision(self, event):
        for bubble, radius in list(reversed(self.bubbles)):
            x1, y1, x2, y2 = self.canvas.coords(bubble)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.canvas.delete(bubble)
                self.bubbles.remove((bubble, radius))
                self.score += 10
                self.score_label.configure(text=f"Score: {self.score}")
                break

    def game_over(self):
        self.cancel_timers()
        self.canvas.create_text(300, 200, text="Game Over!", font=("Helvetica", 24), fill="red")
        self.canvas.unbind("<Button-1>")


def create_gui():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Emotion-Based Music Companion")
    root.geometry("520x360")

    ctk.CTkLabel(root, text="Welcome! Choose an option below:", font=("Helvetica", 16)).pack(pady=20)

    ctk.CTkButton(root, text="Start Camera", command=lambda: detect_emotion(root)).pack(pady=8)
    ctk.CTkButton(root, text="Open Chatbot", command=lambda: open_chatbot(root)).pack(pady=8)
    ctk.CTkButton(root, text="Play Bubble Pop Game", command=lambda: BubbleGame(root)).pack(pady=8)
    ctk.CTkButton(root, text="Exit", command=root.quit).pack(pady=12)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
