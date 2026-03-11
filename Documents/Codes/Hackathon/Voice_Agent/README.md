# SkyItalia AI Voice Agent

## What Is This Project

This project was built for an AI Voice Agent Hackathon. The goal was to create a real voice assistant for SkyItalia, a fictional Italian airline, that can handle full passenger service conversations over the phone.

The assistant is named Sofia. She can understand what a passenger is saying, call live airline APIs to get real data, and respond in a natural human voice. She adapts her tone to match the passenger's mood, detects the language automatically, and handles everything from flight lookups to booking cancellations. When something is truly beyond her authority, she transfers the call to a human supervisor named Marco.

## How It Works

Sofia is built on ElevenLabs Conversational AI, which manages the entire voice pipeline including speech recognition, language detection, and text-to-speech output. The language model powering her reasoning is Gemini 2.0 Flash. When a passenger speaks, the system transcribes the audio, sends the text to the model along with the conversation history, and the model decides what to say or which API to call. The response is then converted back to natural speech using the ElevenLabs multilingual v2 voice model.

The project is structured in phases. Each phase is a standalone Python script that sends configuration updates to the live agent using the ElevenLabs API. There is no need to recreate the agent from scratch to add features. Each script patches only what changed.

## Knowledge Base and RAG

Sofia's knowledge base is built on five policy documents covering baggage rules, flight changes and cancellations, EU compensation policy, the SkyMiles loyalty program, and a general FAQ. During a conversation, whenever a passenger asks a policy question, Sofia retrieves the relevant content from these documents in real time rather than relying on what the language model already knows from training. This keeps her answers grounded in actual airline rules instead of guesses. If SkyItalia updates a policy, the team simply uploads a new document and the agent reflects the change immediately with no retraining needed.

## Multilingual Support

Sofia automatically detects whether a passenger is speaking English, Italian, French, Spanish, or German and switches language immediately without asking. This is handled through a combination of ElevenLabs language presets, an enabled language detection built-in tool, and a strict language rule placed at the top of the system prompt. The language detection tool fires at the start of each conversation and applies the matching language preset, which overrides the model's default response language.

## What Sofia Can Do

Sofia handles the following tasks during a voice call:

1. Look up the status of any flight by flight number
2. Search for available flights between two cities on a given date
3. Check a SkyMiles loyalty account by member ID
4. File a formal passenger complaint and return a reference number
5. Check if a passenger qualifies for EU Regulation 261 compensation
6. Authenticate a passenger using their booking reference and last name
7. Retrieve full booking details after authentication
8. Change the flight date or number on a booking
9. Cancel a booking with proper warnings and passenger confirmation
10. Show available seats and assign a new one
11. Offer a cabin class upgrade with both cash and SkyMiles payment options
12. Transfer the call to supervisor Marco when the situation genuinely requires it

She also understands phonetic spelling in NATO, Italian city, French firstname, and Spanish city alphabets, which passengers commonly use when spelling out booking references over the phone.

## Project Files

### phase1_create_agent.py

This is where everything starts. The script uploads the five knowledge base documents to ElevenLabs and creates the Sofia agent for the first time. It sets up her voice, the initial system prompt, language model settings, and greeting message. After running, it saves the agent ID and knowledge base document IDs into agent_state.json so all subsequent scripts connect to the same agent.

### phase2_add_tools.py

Adds the five public tools that any passenger can trigger without authenticating. These connect Sofia to the live SkyItalia API backend. The tools added here are get_flight_status, search_flights, get_loyalty_info, file_complaint, and check_compensation.

### phase3_add_auth_tools.py

Adds the authentication layer and four protected booking tools. Before a passenger can view or change their booking, they must provide their booking reference and last name. Once verified, Sofia receives an auth token and uses it for all further actions in the call. The tools added here are authenticate_passenger, get_booking, change_booking, and cancel_booking.

### phase4_add_seat_tools.py

Adds seat selection and cabin upgrade capabilities along with a more detailed system prompt that walks Sofia through the exact steps for seat-related tasks. The tools added here are get_available_seats, change_seat, and upgrade_cabin.

### phase5_add_supervisor.py

Introduces the second agent, Marco. This script creates Marco as a separate ElevenLabs agent with his own voice and system prompt, then updates Sofia with a transfer_to_agent tool linked directly to Marco. Sofia is only permitted to use this tool when the passenger is authenticated and the issue genuinely requires human authority.

### phase6_tune_prompt.py

Improves how Sofia speaks without changing any tools. The system prompt is rewritten to include tone-matching rules. Sofia shifts to calm empathy when someone is upset and stays warm and casual when someone is relaxed. Phonetic alphabet support is expanded with complete word lists. Language switching is made automatic and immediate.

### phase7_fix_bugs.py

Fixes conversational bugs found during testing. A TOOL CALL RULES section is added to the prompt telling Sofia to call certain tools immediately as soon as she has the required information, without asking unnecessary follow-up questions. Language switching is also made stricter.

### patch_cancel_fix.py

Patches a specific issue in the cancellation flow. Enforces a strict four-step procedure: warn the passenger that a penalty may apply, ask for explicit confirmation, call the cancel API, and then report only what the API returned. Sofia is prohibited from guessing or inventing any amount before the API responds.

### step1_fix_eur_hallucination.py

Targets a hallucination bug where Sofia was stating specific EUR penalty amounts during cancellation discussions before calling the API. The fix moves the cancellation rules to the very top of the system prompt and defines five explicit rules preventing Sofia from ever inventing a penalty amount, suggesting a travel voucher, or softening a zero-refund outcome with fake alternatives. LLM temperature is also lowered from 0.8 to 0.5 to reduce creative generation during factual operations.

### fix_tools_and_speed.py

A maintenance patch that corrects tool definitions and adjusts response speed settings applied after the main phase scripts.

### recreate_sofia.py

A utility script used to fully recreate or restore Sofia from scratch using the final confirmed system prompt. Useful if the agent configuration becomes inconsistent after many partial patches and needs to be rebuilt cleanly.

### agent_state.json

Generated automatically when Phase 1 runs and updated again in Phase 5. It stores Sofia's agent ID, the list of knowledge base document IDs, and Marco's supervisor agent ID. Every phase script reads this file at startup to stay connected to the same live agent. This file is excluded from version control because it contains live runtime identifiers.

### Knowledge Base Folder

Contains five markdown documents uploaded to ElevenLabs in Phase 1.

**baggage_policy.md** covers checked bag limits by fare class, oversize fees, cabin baggage rules, and special item handling.

**change_cancel_policy.md** explains the fees and rules for changing a flight date or cancelling a booking depending on fare type.

**compensation_policy.md** describes EU Regulation 261/2004 and the compensation amounts passengers are entitled to based on flight distance and disruption type.

**loyalty_program.md** explains the SkyMiles program including membership tiers, how points are earned, and how they can be redeemed.

**faq.md** covers general questions about check-in, travel documents, meals, pets, Wi-Fi, and other common topics.

## Technologies Used

| Tool | Purpose |
|---|---|
| Python | All scripting and API communication |
| requests | Sending HTTP requests to ElevenLabs and the airline backend |
| ElevenLabs Conversational AI | Full voice agent platform handling STT, language detection, LLM orchestration, and TTS |
| Gemini 2.0 Flash | Language model powering Sofia's reasoning and tool decisions |
| ElevenLabs eleven_multilingual_v2 | Text-to-speech engine supporting all five languages |
| ElevenLabs language_presets | Automatic language switching based on detected spoken language |
| SkyItalia API (skyitalia.yellowtest.it) | Live airline backend for flights, bookings, loyalty, and complaints |

## How to Run the Project

Before running anything, make sure you have Python installed and the requests library available.

```
pip install requests
```

You need an ElevenLabs API key. Set it as an environment variable before running any script.

```
export ELEVENLABS_API_KEY=your_key_here
```

Each script currently reads the key from a constant at the top of the file. Replace the value of WRITE_KEY in each script with your own key, or better yet update the scripts to read from os.environ so the key never appears in source code.

Run the scripts in order. Each one builds on the previous.

```
python phase1_create_agent.py
python phase2_add_tools.py
python phase3_add_auth_tools.py
python phase4_add_seat_tools.py
python phase5_add_supervisor.py
python phase6_tune_prompt.py
python phase7_fix_bugs.py
python patch_cancel_fix.py
python step1_fix_eur_hallucination.py
```

After running all steps, Sofia is fully configured and can be tested from the ElevenLabs dashboard. The dashboard link is printed at the end of Phase 1.

## Security Notice

The WRITE_KEY constant in each script currently contains a hardcoded ElevenLabs API key. Before pushing this project to any public repository, replace all hardcoded keys with environment variable reads using os.environ.get("ELEVENLABS_API_KEY"). Never commit a live API key to GitHub. Anyone who finds it can use your account and run up charges.

The agent_state.json file contains live agent IDs. Keep this file local and never commit it. It is already listed in .gitignore.
