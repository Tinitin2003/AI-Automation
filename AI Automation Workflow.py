import speech_recognition
from googleapiclient.discovery import build
import webbrowser
from datetime import datetime, timedelta
import google.generativeai as genai
import re
def is_youtube_url(url):
    pattern = re.compile(
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|embed/|live/|playlist\?list=)?([a-zA-Z0-9_-]{11,})'
    )
    if pattern.search(url):
        return True
    else:
        return False


#get_voice_input function uses the SpeechRecognition library to capture audio from the microphone and convert it to text.

def get_voice_input():
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        print("Please speak something...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except speech_recognition.UnknownValueError:
        print("Sorry, I did not understand that.")
        return None
    except speech_recognition.RequestError as e:
        print(f"Could not request results; {e}")
        return None
get_voice_input()


# search_youtube function uses the YouTube Data API to search for videos based on a query.
def search_youtube(query, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=100,
        publishedAfter=(datetime.now() - timedelta(days=14)).isoformat("T") + "Z"  # 14 days ago (ISO format)
    )
    response = request.execute()
    return response['items']


# Filter videos based on duration (between 4 and 20 minutes)
def parse_duration(iso_duration):
    import isodate
    duration = isodate.parse_duration(iso_duration)
    return duration.total_seconds() / 60
def filter_videos(videos, api_key):
    ids = ",".join([video['id']['videoId'] for video in videos])
    youtube = build("youtube", "v3", developerKey=api_key)
    video_details = youtube.videos().list(part="contentDetails,snippet", id=ids).execute()

    filtered = []
    count=0
    for item in video_details['items']:
        count=count+1
        duration = item['contentDetails']['duration']
        minutes = parse_duration(duration)
        if 4 <= minutes <= 20:
            filtered.append({
                "id": item['id'],
                "title": item['snippet']['title'],
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })
        if count==20:
            break
    return filtered



# Analyzes the video titles

def analyze_with_gemini(titles,links, query, gemini_api_key):
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-pro" if available

    title_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])

    prompt = f"""
You are a helpful assistant analyzing YouTube titles.
User search query: "{query}"

Here are some YouTube video titles:
{title_list}
Here are the corresponding links:
{links}
From these, which one seems the most relevant and high-quality for the user's query?
Just return the number, title and the link of the video that you think is the most relevant.
"""

    response = model.generate_content(prompt)
    prompt_link=f"""{response.text.strip()} just return the link of the video as it will pass through the browser"""
    link=model.generate_content(prompt_link)
    url = link.text.strip()
    if is_youtube_url(url):
        webbrowser.open(url)
    return response.text.strip()



query = get_voice_input()

videos=search_youtube(query,"AIzaSyAwnNaaVN7DUOx7Rgz0cDOROSBBDFT1K0s")
query_result=filter_videos(videos, "AIzaSyAwnNaaVN7DUOx7Rgz0cDOROSBBDFT1K0s")
titles = [video['title'] for video in query_result]
links = [video['url'] for video in query_result]
print(analyze_with_gemini(titles,links, query, "AIzaSyBfym9Q7uZX_2mOEJ0XOQ-E6x1S67WyH58"))