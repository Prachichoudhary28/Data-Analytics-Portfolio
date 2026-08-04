import speech_recognition as sr
import pyttsx3
import webbrowser

import nltk
import datetime
import pyjokes
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageDraw
import threading
import requests
from bs4 import BeautifulSoup
import wikipedia
import yt_dlp

# Optional googlesearch
try:
    from googlesearch import search
except Exception:
    search = None

# Download punkt for sentence splitting
nltk.download('punkt')

recognizer = sr.Recognizer()
engine = pyttsx3.init(driverName='sapi5')

# ---------------- SPEAK + CHAT INSERT ---------------- #
def speak(text):
    chat_insert("Jarvis", text)
    engine.say(text)
    engine.runAndWait()
    

def chat_insert(sender, message):
    chat_area.config(state=tk.NORMAL)
    if sender == "User":
        chat_area.insert(tk.END, f"🧑 {sender}: {message}\n", "user")
    else:
        chat_area.insert(tk.END, f"🤖 {sender}: {message}\n", "jarvis")
    chat_area.config(state=tk.DISABLED)
    chat_area.yview(tk.END)

# ---------------- PROCESS COMMAND ---------------- #
def processCommand(command):
    command = command.lower()

    # ---- Search functionality ----
    if command.startswith("search") or "search for " in command or command.startswith("find "):
        q = command
        for prefix in ("search for ", "search ", "find "):
            if q.startswith(prefix):
                q = q[len(prefix):]
                break
        q = q.strip()

        if not q:
            speak("What would you like me to search for?")
            return

        speak(f"Searching for {q}")
        first_link = None

        # Google search
        try:
            if search:
                try:
                    results = list(search(q, num_results=5))
                except TypeError:
                    results = list(search(q, num=5, stop=5))
                if results:
                    first_link = results[0]
        except Exception:
            first_link = None

        # DuckDuckGo fallback
        if not first_link:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                dd = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=headers, timeout=6)
                soup = BeautifulSoup(dd.text, "html.parser")
                a = soup.find("a", {"class": "result__a"})
                if a and a.get("href"):
                    first_link = a["href"]
            except Exception:
                first_link = None

        if not first_link:
            speak("Sorry, I couldn't find any results for that.")
            return

        speak("Opening the top result I found.")
        webbrowser.open(first_link)

        # Try to summarize
        did_summary = False
        try:
            try:
                summary = wikipedia.summary(q, sentences=2)
            except Exception:
                wsearch = wikipedia.search(q)
                if wsearch:
                    summary = wikipedia.summary(wsearch[0], sentences=2)
                else:
                    raise Exception("No wikipedia page")
            if summary:
                speak(summary)
                did_summary = True
        except Exception:
            did_summary = False

        if not did_summary:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(first_link, headers=headers, timeout=6)
                soup = BeautifulSoup(res.text, "html.parser")

                meta = (soup.find("meta", attrs={"name": "description"}) or
                        soup.find("meta", attrs={"property": "og:description"}))
                if meta and meta.get("content"):
                    text = meta.get("content").strip()
                else:
                    paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
                    text = " ".join(paras)[:3000]

                if text:
                    sents = nltk.sent_tokenize(text)
                    if sents:
                        summary = " ".join(sents[:2])
                        speak(summary)
                    else:
                        speak("I opened the page, but couldn't make a short summary.")
                else:
                    speak("I opened the page, but couldn't find content to summarize.")
            except Exception:
                speak("I opened the page, but couldn't summarize it.")
        return

    # ---- Existing features ----
    if "open google" in command:
        webbrowser.open("https://google.com")
        speak("Opening Google")
    elif "open facebook" in command:
        webbrowser.open("https://facebook.com")
        speak("Opening Facebook")
    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
    elif "open linkedin" in command:
        webbrowser.open("https://linkedin.com")
        speak("Opening LinkedIn")

    # elif command.startswith("play"):
    #     parts = command.split(" ", 1)
    #     if len(parts) > 1:
    #         song = parts[1].strip().lower()
    #         if song in musicLibrary.music:
    #             link = musicLibrary.music[song]
    #             speak(f"Playing {song}")
    #             webbrowser.open(link)
    #         else:
    #             speak("Sorry, I don't have that song in my library")
    #     else:
    #         speak("Please tell me which song to play")

    elif command.startswith("play"):

       song = command.replace("play", "").strip()

       if not song:
        speak("Please tell me the song name.")
        return

       speak(f"Searching YouTube for {song}")

       try:
        ydl_opts = {
            "quiet": True,
            "default_search": "ytsearch1",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song, download=False)

            if "entries" in info:
                video = info["entries"][0]
            else:
                video = info

            webbrowser.open(video["webpage_url"])
            speak(f"Now playing {video['title']}")

       except Exception as e:
        print(e)
        speak("Sorry, I couldn't find that song.")

    elif "time" in command:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {t}")

    elif "date" in command:
        date = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today's date is {date}")

    elif "joke" in command:
        joke = pyjokes.get_joke()
        speak(joke)

    elif "your name" in command:
        speak("I am Jarvis, your personal assistant.")

    else:
        speak("Sorry, I did not get that.")

# ---------------- LISTENING ---------------- #
def listen_command():
    try:
        start_animation()
        with sr.Microphone() as source:
            speak("Listening...")
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
            command = recognizer.recognize_google(audio)
            chat_insert("User", command)
            processCommand(command)
    except Exception:
        speak("Sorry, I couldn’t hear you properly.")
    finally:
        stop_animation()

# ---------------- GUI ---------------- #
root = tk.Tk()
root.title("Jarvis AI Assistant")
root.configure(bg="#1e1e2e")
root.geometry("500x650")

# Canvas for Ripple + Avatar
canvas = tk.Canvas(root, width=200, height=200, bg="#1e1e2e", highlightthickness=0)
canvas.pack(pady=10)

# Load Jarvis Avatar
base_img = Image.open("jarvis.png")  # Replace with your Jarvis image
base_img = base_img.resize((120, 120))
avatar_img = ImageTk.PhotoImage(base_img)
avatar = canvas.create_image(100, 100, image=avatar_img)

# Animation flags
animating = [False]
ripple_circles = []

def draw_ripple(radius, alpha):
    img = Image.new("RGBA", (200, 200), (30, 30, 46, 0))
    draw = ImageDraw.Draw(img)
    color = (100, 200, 255, alpha)
    draw.ellipse((100-radius, 100-radius, 100+radius, 100+radius), outline=color, width=3)
    return ImageTk.PhotoImage(img)

def animate_ripple(step=0):
    if not animating[0]:
        return
    canvas.delete("ripple")

    for i in range(3):  # 3 ripple layers
        radius = (step + i*20) % 120
        alpha = max(0, 200 - radius*2)
        ripple = draw_ripple(radius, alpha)
        canvas.create_image(100, 100, image=ripple, tags="ripple")
        ripple_circles.append(ripple)

    scale = 1.0 + 0.1 * (step % 10) / 5
    new_size = int(120 * scale)
    resized = base_img.resize((new_size, new_size))
    new_avatar = ImageTk.PhotoImage(resized)
    canvas.itemconfig(avatar, image=new_avatar)
    canvas.image = new_avatar

    root.after(100, animate_ripple, step+5)

def start_animation():
    animating[0] = True
    animate_ripple()

def stop_animation():
    animating[0] = False
    canvas.delete("ripple")
    canvas.itemconfig(avatar, image=avatar_img)
    canvas.image = avatar_img

# Chat display area
chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), bg="#2e2e3e", fg="white")
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_area.tag_config("user", foreground="#7aa2f7")
chat_area.tag_config("jarvis", foreground="#9ece6a")
chat_area.config(state=tk.DISABLED)

# Round Mic Button
def on_mic_click():
    threading.Thread(target=listen_command).start()

mic_img = Image.open("mic.png")  # Replace with a mic image
mic_img = mic_img.resize((60, 60))
mic_icon = ImageTk.PhotoImage(mic_img)

mic_button = tk.Button(root, image=mic_icon, command=on_mic_click,
                       bd=0, bg="#1e1e2e", activebackground="#1e1e2e")
mic_button.pack(pady=15)

# Init
speak("Initializing Jarvis...")

root.mainloop()











































































