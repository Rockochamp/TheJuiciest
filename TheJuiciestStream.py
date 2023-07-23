import openai
import os
import json
import requests
from git import Repo
import os

# Get the path of the currently running script
repo_path = os.path.dirname(os.path.abspath(__file__))

# Create a repo object
repo = Repo(repo_path)

# Add all files in the repository to the staging area
repo.git.add('.')

openai.api_key = os.getenv("OPENAI_API_KEY")

# Read the personas from the JSON file
with open('personas.json', 'r') as file:
    personas = json.load(file)

# Eleven Labs TTS API base url and headers
base_url = "https://api.elevenlabs.io/v1/text-to-speech"
headers = {
  "Accept": "audio/mpeg",
  "Content-Type": "application/json",
  "xi-api-key": "a14b14551b6bcde1929b9e8065223b7f"
}

def text_to_speech(voice_id, text, directory):
    # Set up the request data
    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
      }
    }

    # Make the POST request
    response = requests.post(f"{base_url}/{voice_id}", json=data, headers=headers)

     # Create the directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the response audio stream as an MP3 file
    with open(os.path.join(directory, f"{voice_id}.mp3"), 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns):
    # Initialize separate conversation logs for each assistant
    chat_log1 = [{'role':'system', 'content': system_behavior1}]
    chat_log2 = [{'role':'system', 'content': system_behavior2}]

    # List to hold the combined conversation
    combined_chat_log = []

    for i in range(num_turns):
        if i % 2 == 0:
            # It's user1's turn
            chat_log1.append({'role':'user', 'content': start_message, 'name': 'user1'})
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=chat_log1
            )
            start_message = response['choices'][0]['message']['content']
            chat_log2.append({'role':'user', 'content': start_message, 'name': 'user1'})
            combined_chat_log.append({'role':'user', 'content': start_message, 'name': 'user1'})
            
            # Convert the text to speech and save it as an MP3 file
            text_to_speech('9kHGro8I4HpLZLYw5af1', start_message, 'bot1')
           
            # Commit and Push the changes
            repo.git.commit('-m', 'Bot Speeches uploaded ')
            repo.git.push()
        else:
            # It's user2's turn
            chat_log2.append({'role':'user', 'content': start_message, 'name': 'user2'})
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=chat_log2
            )
            start_message = response['choices'][0]['message']['content']
            chat_log1.append({'role':'user', 'content': start_message, 'name': 'user2'})
            combined_chat_log.append({'role':'user', 'content': start_message, 'name': 'user2'})
            
            # Convert the text to speech and save it as an MP3 file
            text_to_speech('484qCysiNIYp5zQ0Ig7v', start_message, 'bot2')
            
            # Commit and Push the changes
            repo.git.commit('-m', 'Bot Speeches uploaded ')
            repo.git.push()


    return combined_chat_log

# Specify system behaviors
system_behavior1 = personas['Hasan Abibi']
system_behavior2 = personas['Andrew Fake']

# Start message
start_message = 'Hello, how are you?'

# Number of turns in the conversation
num_turns = 10

combined_chat_log = chat_with_gpt3(system_behavior1, system_behavior2, start_message, num_turns)

for message in combined_chat_log:
    print(f"{message['name']}: {message['content']}")
