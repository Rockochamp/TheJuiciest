import openai
import os
import json
import requests
from git import Repo
import time
import irc.bot
import random
import re
from threading import Thread

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, token, channel):
        server = 'irc.chat.twitch.tv'
        port = 6667
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username)
        self.channel = '#' + channel
        self.questions = []

    def on_welcome(self, connection, event):
        connection.join(self.channel)
        print(f"Connected")

    def on_pubmsg(self, connection, event):
        username = event.source.split('!')[0]  # Extracting the username from the event
        message = event.arguments[0]
        if self.is_question(message):
            question_with_username = f"{username}: {message}"  # Including the username in the question
            self.questions.append(question_with_username)
            print(f"Added question: {question_with_username}")

    @staticmethod
    def is_question(message):
        return bool(re.search(r'\?$', message))

def git_push():
    repo_path = os.path.dirname(os.path.abspath(__file__))
    repo = Repo(repo_path)
    repo.git.add(A=True)
    if repo.is_dirty():
        repo.git.commit('-m', 'Bot Speeches uploaded')
        repo.git.push()
    else:
        print("No changes to commit")

def check_queue(directory):
    while len(os.listdir(directory)) > 2:
        print(f"Waiting... {len(os.listdir(directory))} files in the queue.")
        time.sleep(1)

def text_to_speech(label, voice_id, text, turn):
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", json=data, headers={
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
    })
    if not os.path.exists(label):
        os.makedirs(label)
    with open(os.path.join(label, f"{label}_{turn}.mp3"), 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns, bot):
    chat_log1 = [{'role': 'system', 'content': system_behavior1}]
    chat_log2 = [{'role': 'system', 'content': system_behavior2}]
    combined_chat_log = []

    for i in range(num_turns):
        if bot.questions and random.random() < 1:
            question_with_username = random.choice(bot.questions)
            bot.questions.remove(question_with_username)
            print(f"Answering Twitch question: {question_with_username}")

            # Determine which persona should answer (modify as needed)
            if 'Andrew' in question_with_username:
                responder = chat_log2
                commenter = chat_log1
            if 'Hasan'  in question_with_username:
                responder = chat_log1
                commenter = chat_log2

            responder.append({'role': 'user', 'content': question_with_username, 'name': 'TwitchUser'})
            response = openai.ChatCompletion.create(model="gpt-4", messages=responder)
            answer = response['choices'][0]['message']['content']

            # Add comments from the other persona
            commenter.append({'role': 'user', 'content': answer, 'name': 'Assistant'})
            response_comment = openai.ChatCompletion.create(model="gpt-4", messages=commenter)
            comment = response_comment['choices'][0]['message']['content']

            # Combine answer and comment
            combined_answer = f"{answer}\n{comment}"

            # Add to combined chat log
            combined_chat_log.append({'role': 'user', 'content': combined_answer, 'name': 'Assistant'})


        if i % 2 == 0:
            chat_log1.append({'role': 'user', 'content': start_message, 'name': 'user1'})
            response = openai.ChatCompletion.create(model="gpt-4", messages=chat_log1)
            start_message = response['choices'][0]['message']['content']
            chat_log2.append({'role': 'user', 'content': start_message, 'name': 'user1'})
            combined_chat_log.append({'role': 'user', 'content': start_message, 'name': 'user1'})
            check_queue('bot1')
            text_to_speech('bot1', '9kHGro8I4HpLZLYw5af1', start_message, i // 2)
            git_push()
        else:
            chat_log2.append({'role': 'user', 'content': start_message, 'name': 'user2'})
            response = openai.ChatCompletion.create(model="gpt-4", messages=chat_log2)
            start_message = response['choices'][0]['message']['content']
            chat_log1.append({'role': 'user', 'content': start_message, 'name': 'user2'})
            combined_chat_log.append({'role': 'user', 'content': start_message, 'name': 'user2'})
            check_queue('bot2')
            text_to_speech('bot2', '484qCysiNIYp5zQ0Ig7v', start_message, i // 2)
            git_push()

    return combined_chat_log

def main():
    # Create the TwitchBot instance
    bot = TwitchBot('rockochamp', os.getenv("TWITCH_OAUTH_TOKEN"), 'Rockochamp')

    # Define the threaded function to run the bot
    def run_twitch_bot():
        bot.start()

    # Start the threaded function
    twitch_bot_thread = Thread(target=run_twitch_bot)
    twitch_bot_thread.start()

    # Wait a bit to ensure the bot has connected (adjust as needed)
    time.sleep(5)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open('personas.json', 'r') as file:
        personas = json.load(file)

    system_behavior1 = personas['Hasan Abibi']
    system_behavior2 = personas['Andrew Fake']
    start_message = 'Hello, how are you?'
    num_turns = 6

    # Pass the same bot instance to chat_with_gpt3
    combined_chat_log = chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns, bot)

    for message in combined_chat_log:
        print(f"{message['name']}: {message['content']}")

if __name__ == "__main__":
    main()