import pyttsx3
import requests
from datetime import datetime
import os
import sys
import platform
import psutil
import schedule
import time
from plyer import notification
import threading
from bs4 import BeautifulSoup
from random import choice
import speech_recognition as sr
from googlesearch import search

# Define USER and BOTNAME
USERNAME = 'Sir'
BOTNAME = 'Jarvis'

# Initialize the speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Female voice

# Global variables to keep track of the assistant's state
assistant_active = True
stop_listening = threading.Event()
stop_listening.set()  # Initially, the assistant is listening for the wake word

def speak(text):
    """Converts text to speech"""
    engine.say(text)
    engine.runAndWait()

def greet_user():
    """Greets the user according to the time"""
    hour = datetime.now().hour
    if 6 <= hour < 12:
        greeting = f"Good Morning {USERNAME}"
    elif 12 <= hour < 16:
        greeting = f"Good Afternoon {USERNAME}"
    elif 16 <= hour < 19:
        greeting = f"Good Evening {USERNAME}"
    else:
        greeting = f"Good Night {USERNAME}"
    speak(f"{greeting}")

def get_weather(city):
    coordinates = {
        'london': (51.52, -0.13),
        'new york': (40.71, -74.01),
        'paris': (48.85, 2.35),
        'alter': (51.52, 3.41)
    }
    city = city.lower()
    if city not in coordinates:
        return "Sorry, I don't have weather information for that location."

    latitude, longitude = coordinates[city]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 1
    }
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()
        daily = response.get("daily", {})
        weather_code = daily.get("weathercode", [0])[0]
        precipitation_sum = daily.get("precipitation_sum", [0])[0]
        temp_max = daily.get("temperature_2m_max", [0])[0]
        temp_min = daily.get("temperature_2m_min", [0])[0]

        weather_description = {
            0: 'Clear',
            1: 'Mainly clear',
            2: 'Partly cloudy',
            3: 'Overcast',
            4: 'Fog',
            5: 'Depositing rime fog',
            6: 'Drizzle',
            7: 'Freezing drizzle',
            8: 'Showers of rain',
            9: 'Snow showers',
            10: 'Rain',
            11: 'Snow',
            12: 'Rain and snow',
            13: 'Thunderstorms',
            14: 'Thunderstorms with hail',
        }
        weather = weather_description.get(weather_code, 'Unknown')
        return (f"The weather in {city.title()} is currently {weather} with a precipitation of {precipitation_sum} mm. "
                f"The maximum temperature is {temp_max}°C and the minimum temperature is {temp_min}°C.")
    except Exception as e:
        return f"Error retrieving weather data: {str(e)}"

def send_notification(reminder):
    """Sends a notification for the reminder"""
    notification.notify(
        title="Reminder",
        message=reminder,
        timeout=10  # Notification will stay for 10 seconds
    )

def set_reminder(reminder, reminder_time):
    """Sets a reminder for the user"""
    def job():
        send_notification(reminder)
    
    schedule.every().day.at(reminder_time).do(job)

    # Run scheduler in a separate thread
    def scheduler_thread():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    threading.Thread(target=scheduler_thread, daemon=True).start()
    return f"Reminder set for {reminder_time}: {reminder}"

def check_system_status():
    """Checks and returns basic system status"""
    os_name = platform.system()
    cpu_info = platform.processor()
    ram_info = f"{round(psutil.virtual_memory().total / (1024 ** 3))} GB"
    return f"System is running {os_name} with CPU {cpu_info} and {ram_info} of RAM."

def perform_calculation(query):
    """Performs basic arithmetic calculations"""
    try:
        expression = query.replace('plus', '+').replace('minus', '-').replace('x', '*').replace('divided by', '/')
        result = eval(expression)
        return f"The result of {query} is {result}."
    except Exception as e:
        return f"Error performing calculation: {str(e)}"

def web_search(query):
    """Performs a web search using Google"""
    search_url = f"https://www.google.com/search?q={query}"
    return f"Here are the search results for '{query}': {search_url}"

def get_news():
    """Fetches latest news headlines using News API"""
    api_key = 'acc3b242b619422896ef92dfd8f7043f'  # Replace with your News API key
    
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
    
    try:
        speak('''I'm looking into it sir...''')
        response = requests.get(url).json()
        articles = response.get('articles', [])
        if not articles:
            return "No news articles found."
        
        headlines = [article['title'] for article in articles[:5]]  # Get top 5 headlines
        
        news_formatted = "Here are the latest news headlines:\n"
        for i, headline in enumerate(headlines, 1):
            news_formatted += f"{i}. {headline}\n"
        
        return news_formatted
    except Exception as e:
        return f"Error retrieving news: {str(e)}"

def tell_joke():
    """Tells a random joke"""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the math book look sad? Because it had too many problems.",
        "Why was the computer cold? It left its Windows open.",
        "What do you call fake spaghetti? An impasta!"
    ]
    return choice(jokes)

def get_definition(word):
    """Fetches the definition of a word from an online dictionary"""
    url = f"https://www.dictionary.com/browse/{word}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    definition = soup.find('span', class_='one-click-content')
    if definition:
        return f"The definition of {word} is: {definition.get_text()}"
    else:
        return "Sorry, I couldn't find a definition for that word."

def convert_units(query):
    """Converts units based on the user's query"""
    
    # Define conversion functions
    conversions = {
        'km to miles': lambda km: km * 0.621371,
        'miles to km': lambda miles: miles / 0.621371,
        'kg to pounds': lambda kg: kg * 2.20462,
        'pounds to kg': lambda pounds: pounds / 2.20462,
        'celsius to fahrenheit': lambda c: (c * 9/5) + 32,
        'fahrenheit to celsius': lambda f: (f - 32) * 5/9
    }
    
    # Iterate over conversion types
    for conversion, func in conversions.items():
        if conversion in query:
            try:
                amount = float(query.split()[1])  # Extract the amount to convert
                return f"{amount} {conversion.split(' ')[0]} is equal to {func(amount):.2f} {conversion.split(' ')[-1]}."
            except ValueError:
                return "Sorry, I couldn't understand the amount to convert."
    
    return "Sorry, I don't understand the unit conversion request."

def manage_tasks(command):
    """Add, list, or complete tasks"""
    task_file = 'tasks.txt'

    if 'add task' in command:
        task = command.split('add task')[-1].strip()
        with open(task_file, 'a') as file:
            file.write(task + '\n')
        return f"Task '{task}' added to your to-do list."

    elif 'list tasks' in command:
        if not os.path.exists(task_file):
            return "You have no tasks in your to-do list."
        with open(task_file, 'r') as file:
            tasks = file.readlines()
        tasks = [task.strip() for task in tasks]
        if tasks:
            return "Your to-do list:\n" + "\n".join(f"- {task}" for task in tasks)
        else:
            return "Your to-do list is empty."

    elif 'complete task' in command:
        task = command.split('complete task')[-1].strip()
        if not os.path.exists(task_file):
            return "No tasks file found."
        
        with open(task_file, 'r') as file:
            tasks = file.readlines()

        if task + '\n' in tasks:
            tasks.remove(task + '\n')
            with open(task_file, 'w') as file:
                file.writelines(tasks)
            return f"Task '{task}' marked as complete."
        else:
            return f"Task '{task}' not found in your to-do list."
    
    return "Sorry, I didn't understand your task management request."

def get_summary(term):
    """Fetches a concise summary of a term from Wikipedia"""
    url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{term}'
    try:
        response = requests.get(url).json()
        if 'extract' in response:
            return response['extract']
        else:
            return f"Sorry, no information found for '{term}'."
    except Exception as e:
        return f"Error retrieving summary: {str(e)}"

def listen_for_wake_word():
    """Listens for the wake word to activate the assistant"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for wake word...")
        while True:
            try:
                recognizer.pause_threshold = 1.5  # Adjust this as needed
                audio = recognizer.listen(source)

                query = recognizer.recognize_google(audio, language='en-US').lower()
                print('Detected query:', query)

                if 'hey jarvis' in query:
                    speak("Hello Sir, how can I assist you?")
                    stop_listening.clear()  # Stop listening for wake word
                    global assistant_active
                    assistant_active = True
                    return
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                speak("Sorry, I'm having trouble connecting to the speech recognition service.")
                continue
            except Exception as e:
                print(f"Error occurred: {e}")
                speak("Sorry, something went wrong.")
                continue

def execute_command(command):
    global assistant_active  # Declare global at the start of the function
    
    if 'time' in command:
        return datetime.now().strftime("The time is %H:%M:%S")
    elif 'weather' in command:
        city = command.split('weather in')[-1].strip()
        return get_weather(city)
    elif 'open' in command:
        app = command.split('open')[-1].strip()
        try:
            if os.name == 'nt':  # Windows
                if 'overwatch' in app.lower():
                    os.system('start "" "C:\\Users\\Public\\Desktop\\Overwatch.lnk"')
                elif 'counter' in app.lower():
                    os.system('start "" "C:\\Users\\desme\\OneDrive\\Bureaublad\\Counter-Strike 2.url"')
                else:
                    os.system(f'start {app}')
            elif os.name == 'posix':  # macOS or Linux
                os.system(f'open {app}' if sys.platform == 'darwin' else f'xdg-open {app}')
            return f"Opening {app}."
        except Exception as e:
            return f"Could not open {app}. Error: {str(e)}"
    elif 'reminder' in command:
        parts = command.split('reminder')
        reminder = parts[-1].strip()
        reminder_time = input("Please enter the time for the reminder (format: HH:MM): ")
        return set_reminder(reminder, reminder_time)
    elif 'system status' in command:
        return check_system_status()
    elif 'calculate' in command:
        calculation_query = command.split('calculate')[-1].strip()
        return perform_calculation(calculation_query)
    elif 'search' in command:
        query = command.split('search')[-1].strip()
        return web_search(query)
    elif 'news' in command:
        return get_news()
    elif 'joke' in command:
        return tell_joke()
    elif 'define' in command:
        word = command.split('define')[-1].strip()
        return get_definition(word)
    elif 'convert' in command:
        return convert_units(command)
    elif 'task' in command:
        return manage_tasks(command)
    elif 'thanks' in command or 'thank you' in command:
        return f'You are welcome {USERNAME}'
    elif 'jarvis sleep' in command:
        assistant_active = False  # Modify the global variable here
        stop_listening.set()  # Start listening for the wake word again
        return "Going to sleep. Say 'Hey Jarvis' to wake me up."
    elif 'jarvis wake up' in command:
        assistant_active = True  # Modify the global variable here
        stop_listening.clear()  # Stop listening for the wake word
        return "I'm awake. How can I assist you?"
    else:
        try:
            results = search(command)  # Adjust the number of results as needed
            result_texts = []
            for result in results:
                result_texts.append(f"Title: {result.title}\nURL: {result.url}\nSnippet: {result.snippet}\n")
            return "\n".join(result_texts)
        except Exception as e:
            return f"An error occurred: {e}"

def take_user_input():
    """Takes user input through speech"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1.5  # Adjust this as needed
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-US')
        print(f"User said: {query}")
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
        speak("Sorry, I did not catch that. Could you please repeat?")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        speak("Sorry, I'm having trouble connecting to the speech recognition service.")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        speak("Sorry, something went wrong.")
        return None

    return query.lower()

def main():
    greet_user()
    global stop_listening
    while True:
        if stop_listening.is_set():
            listen_for_wake_word()
        elif not stop_listening.is_set() and assistant_active:
            command = take_user_input()
            if command:
                response = execute_command(command)
                if response:
                    print(response)
                    speak(response)

if __name__ == "__main__":
    main()
