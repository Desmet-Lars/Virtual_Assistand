import pyttsx3
import speech_recognition as sr
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

# Define USER and BOTNAME
USERNAME = 'Sir'
BOTNAME = 'Jarvis'

# Initialize the speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Female voice

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
    speak(f"{greeting}. How may I assist you?")

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
        "daily": "weathercode,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 1
    }
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()
        daily = response.get("daily", {})
        weather_code = daily.get("weathercode", [0])[0]
        precipitation_sum = daily.get("precipitation_sum", [0])[0]

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
        return f"The weather in {city.title()} is currently {weather} with a precipitation of {precipitation_sum} mm."
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
    """Fetches latest news headlines"""
    news_url = "https://news.google.com"
    response = requests.get(news_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.find_all('h3', limit=5)
    news_list = [headline.get_text() for headline in headlines]
    return "Here are the latest news headlines: " + ", ".join(news_list)

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
    """Converts units of measurement"""
    conversions = {
        'km to miles': lambda x: x * 0.621371,
        'miles to km': lambda x: x / 0.621371,
        'celsius to fahrenheit': lambda x: (x * 9/5) + 32,
        'fahrenheit to celsius': lambda x: (x - 32) * 5/9
    }
    for conversion, func in conversions.items():
        if conversion in query:
            amount = float(query.split(' ')[0])
            return f"{amount} {conversion.split(' ')[0]} is equal to {func(amount):.2f} {conversion.split(' ')[-1]}."
    return "Sorry, I don't understand the unit conversion request."

def manage_tasks(command):
    """Add or list tasks"""
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
        return "Your to-do list: " + ", ".join(tasks)
    return "I can only add or list tasks. Please use 'add task' or 'list tasks'."

def take_user_input():
    """Takes user input, recognizes it using Speech Recognition module and converts it into text"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening....')
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=10)
        except sr.WaitTimeoutError:
            speak("Listening timed out, please try again.")
            return None

    if audio:
        try:
            print('Recognizing...')
            query = r.recognize_google(audio, language='en-in')
            print(query)
            return query
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
        except sr.RequestError:
            speak("Sorry, there was an error with the speech recognition service.")
        return None

def execute_command(command):
    """Executes the command based on the user input"""
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
    else:
        return "Sorry, I didn't understand that command."

def main():
    greet_user()
    while True:
        command = take_user_input()
        if command:
            response = execute_command(command)
            if response:
                speak(response)
                print(response)

if __name__ == "__main__":
    main()
