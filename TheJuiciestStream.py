import openai
import os
import json
import requests
from git import Repo
import time

def git_push():
    repo_path = os.path.dirname(os.path.abspath(__file__))
    repo = Repo(repo_path)
    repo.git.add(A=True)  # This is equivalent to `git add -A`
    if repo.is_dirty():
        repo.git.commit('-m', 'Bot Speeches uploaded')
        repo.git.push()
    else:
        print("No changes to commit")

def check_queue(directory):
    while len(os.listdir(directory)) > 1:
        print(f"Waiting... {len(os.listdir(directory))} files in the queue.")
        time.sleep(5)

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

def chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns):
    chat_log1 = [{'role':'system', 'content': system_behavior1}]
    chat_log2 = [{'role':'system', 'content': system_behavior2}]
    combined_chat_log = []

    for i in range(num_turns):
        if i % 2 == 0:
            chat_log1.append({'role':'user', 'content': start_message, 'name': 'user1'})
            response = openai.ChatCompletion.create(model="gpt-4", messages=chat_log1)
            start_message = response['choices'][0]['message']['content']
            chat_log2.append({'role':'user', 'content': start_message, 'name': 'user1'})
            combined_chat_log.append({'role':'user', 'content': start_message, 'name': 'user1'})
            text_to_speech('bot1', '9kHGro8I4HpLZLYw5af1', start_message, i // 2)
            check_queue('bot1')
            git_push()
        else:
            chat_log2.append({'role':'user', 'content': start_message, 'name': 'user2'})
            response = openai.ChatCompletion.create(model="gpt-4", messages=chat_log2)
            start_message = response['choices'][0]['message']['content']
            chat_log1.append({'role':'user', 'content': start_message, 'name': 'user2'})
            combined_chat_log.append({'role':'user', 'content': start_message, 'name': 'user2'})
            text_to_speech('bot2', '484qCysiNIYp5zQ0Ig7v', start_message, i // 2)
            check_queue('bot2')
            git_push()

    return combined_chat_log

openai.api_key = os.getenv("OPENAI_API_KEY")

with open('personas.json', 'r') as file:
    personas = json.load(file)

system_behavior1 = personas['Hasan Abibi']
system_behavior2 = personas['Andrew Fake']
start_message = 'Hello, how are you?'
num_turns = 10

combined_chat_log = chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns)

for message in combined_chat_log:
    print(f"{message['name']}: {message['content']}")