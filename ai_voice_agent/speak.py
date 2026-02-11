import os
import subprocess
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from io import BytesIO

# Load API key
load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

client = ElevenLabs(api_key=api_key)

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

text = input("Enter text to speak: ")

# Generate MP3 audio
audio_generator = client.text_to_speech.convert(
    voice_id=VOICE_ID,
    model_id="eleven_multilingual_v2",
    text=text
)

audio_bytes = b"".join(audio_generator)

# Save to file
filename = "output.mp3"
with open(filename, "wb") as f:
    f.write(audio_bytes)

# Play using macOS built-in player
subprocess.run(["afplay", filename])

print("Done ✅")