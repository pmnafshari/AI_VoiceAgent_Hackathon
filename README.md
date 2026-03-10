# SkyItalia AI Voice Agent

## What Is This Project

This project was built for an AI Voice Agent Hackathon. The goal was to create a real voice assistant for SkyItalia, a fictional Italian airline, that can talk to passengers over the phone and actually help them with their travel needs.

The assistant is named Sofia. She can understand what a passenger is saying, call live airline APIs to get real data, and respond in a natural human voice. She does not sound like a robot. She adapts her tone, detects the passenger's language automatically, and handles everything from flight lookups to booking cancellations.

There is also a second agent named Marco. Marco is a senior supervisor who Sofia can transfer a call to when a situation is beyond her authority.

---

## How It Works

Sofia is built on top of ElevenLabs Conversational AI, which handles the voice pipeline. The language brain is powered by Gemini 3 Flash. When a passenger speaks, the system transcribes the audio, sends it to the language model, and the model decides what to say or what API to call. The response is then converted back to natural speech using ElevenLabs TTS.

The project is built in phases. Each phase is a standalone Python script that sends configuration updates to the live agent using the ElevenLabs API. There is no need to recreate the agent from scratch to add new features. Each script patches only what changed.

---

## What Sofia Can Do

Sofia handles the following tasks during a voice call:

1. Look up the status of any flight by flight number
2. Search for available flights between two cities on a given date
3. Check a SkyMiles loyalty account by member ID
4. File a formal passenger complaint and return a complaint reference number
5. Check if a passenger qualifies for EU Regulation 261 compensation
6. Authenticate a passenger using their booking reference and last name
7. Retrieve full booking details after authentication
8. Change the flight date or flight number on a booking
9. Cancel a booking with proper warnings and passenger confirmation
10. Show available seats and assign a new seat
11. Offer a cabin class upgrade with both cash and SkyMiles payment options
12. Transfer the call to supervisor Marco when the situation requires it

Sofia supports English, Italian, French, and Spanish. She switches language automatically the moment a passenger speaks in a different language. She also understands phonetic spelling in NATO, Italian city, French firstname, and Spanish city alphabets, which passengers often use when spelling out booking references over the phone.

---

## Project Files

### phase1_create_agent.py

This is where everything starts. This script uploads the five knowledge base documents to ElevenLabs and creates the Sofia agent for the first time. It sets up her voice, her initial system prompt, the language model settings, and her greeting message. After running, it saves the agent ID and knowledge base document IDs into agent_state.json so all other scripts can connect to the same agent.

Functions in this file:

**upload_knowledge_base** reads each markdown document from the knowledge base folder and uploads it to ElevenLabs so Sofia can answer policy questions accurately.

**create_agent** sends the full agent configuration to ElevenLabs and creates Sofia on the platform.

**save_state** writes the agent ID and knowledge base IDs to agent_state.json for use in later phases.

---

### phase2_add_tools.py

This script adds the five public tools to Sofia. These are tools that any passenger can trigger without needing to authenticate. The tools connect Sofia to the live SkyItalia API backend at skyitalia.yellowtest.it.

The tools added in this phase are get_flight_status, search_flights, get_loyalty_info, file_complaint, and check_compensation.

**update_agent_tools** sends a PATCH request to the ElevenLabs API to attach the new tools to Sofia without changing anything else.

---

### phase3_add_auth_tools.py

This script adds the authentication layer and the four protected booking tools. Before a passenger can see or change their booking, they must provide their booking reference and last name. Once verified, Sofia receives an auth token and uses it for all further actions in the call.

The tools added here are authenticate_passenger, get_booking, change_booking, and cancel_booking.

**update_agent** sends the combined list of Phase 2 and Phase 3 tools to the agent together so nothing is overwritten.

---

### phase4_add_seat_tools.py

This script adds seat selection and cabin upgrade capabilities along with a more detailed system prompt that walks Sofia through the exact steps she should follow for each seat-related task.

The tools added here are get_available_seats, change_seat, and upgrade_cabin.

**update_agent** patches both the full tool list and the updated system prompt at the same time, keeping the knowledge base links intact.

---

### phase5_add_supervisor.py

This script introduces the second agent, Marco. It first creates Marco as a separate ElevenLabs agent with his own voice and system prompt. Then it updates Sofia with a special transfer_to_agent tool that links her directly to Marco. Sofia is only allowed to use this tool if the passenger is authenticated and the issue genuinely requires human authority.

**create_supervisor_agent** creates the Marco agent on the ElevenLabs platform with his own voice and configuration.

**update_sofia** adds the transfer tool and the full updated tool list to Sofia.

**save_state** appends Marco's agent ID to agent_state.json.

---

### phase6_tune_prompt.py

This script improves how Sofia speaks without changing any tools. The system prompt is rewritten to include strict tone-matching rules. Sofia is told to be warm and casual when a passenger is relaxed, to shift to calm empathy when someone is upset, and to never stay formally stiff when someone is clearly joking. Phonetic alphabet support is expanded with the complete word list for all four systems. Language switching is made automatic and immediate.

**update_agent** patches only the system prompt while leaving all tools and knowledge base references unchanged.

---

### phase7_fix_bugs.py

This script fixes specific conversational bugs found during testing. A new section called TOOL CALL RULES is added to the prompt. It tells Sofia to call certain tools immediately as soon as she has the required information, without asking unnecessary follow-up questions. For example, she should call get_flight_status the moment a flight number is given, not ask extra questions first. Language switching is also made stricter here.

**update_agent** pushes the corrected prompt and tool list to the live agent.

---

### patch_cancel_fix.py

This script patches a specific issue in the cancellation flow. It enforces a strict four-step procedure: warn the passenger that a penalty may apply, ask for explicit confirmation, call the cancel API, and then report only what the API returned. No amounts should be guessed or invented before the API responds.

**update_agent** applies the cancellation-focused prompt patch to the live agent.

---

### step1_fix_eur_hallucination.py

This script targets a hallucination bug where Sofia was incorrectly stating specific EUR penalty amounts during cancellation discussions even before calling the API. The fix moves the cancellation rules to the very top of the system prompt so they have the highest priority in the model context. Five explicit rules are defined to prevent Sofia from ever inventing a penalty amount, suggesting a travel voucher, or softening a zero-refund outcome with fake alternatives. The LLM temperature is also lowered from 0.8 to 0.5 to reduce creative generation during factual operations.

**update_agent** pushes the corrected high-priority cancellation rules and lower temperature setting to Sofia.

---

### agent_state.json

This file is generated automatically when Phase 1 runs and updated again in Phase 5. It stores Sofia's agent ID, the list of knowledge base document IDs, and Marco's supervisor agent ID. Every phase script reads from this file at startup so all scripts stay connected to the same agent.

This file is excluded from version control via .gitignore because it may contain sensitive runtime identifiers.

---

### Knowledge Base Folder

The Knowledge Base folder contains five markdown documents that Sofia uses to answer passenger questions accurately. These documents are uploaded to ElevenLabs in Phase 1.

**baggage_policy.md** covers what passengers are allowed to bring, checked bag limits by fare class, oversize fees, and special item rules.

**change_cancel_policy.md** explains the rules and fees for changing a flight date or cancelling a booking depending on fare type.

**compensation_policy.md** describes EU Regulation 261/2004 and the compensation amounts passengers are entitled to based on the distance of their disrupted flight.

**loyalty_program.md** explains the SkyMiles program including membership tiers, how points are earned, and how they can be redeemed.

**faq.md** covers general questions about check-in procedures, travel documents, meals, pets, Wi-Fi on board, and other common topics.

---

## Technologies Used

| Tool | Purpose |
|---|---|
| Python | All scripting and API communication |
| requests library | Sending HTTP requests to ElevenLabs and the airline backend |
| ElevenLabs Conversational AI | Full voice agent platform handling STT, LLM, and TTS |
| Gemini 3 Flash Preview | Language model powering Sofia's reasoning |
| ElevenLabs eleven_turbo_v2 | Text-to-speech engine for Sofia and Marco's voices |
| SkyItalia API (skyitalia.yellowtest.it) | Live airline backend for flights, bookings, loyalty, and complaints |

---

## How to Run the Project

Before running anything, make sure you have Python installed and the requests library available. You can install it by running:

```
pip install requests
```

Run the scripts in order. Each script builds on the previous one.

**Step 1** Run phase1_create_agent.py to upload the knowledge base and create Sofia. This generates agent_state.json automatically.

**Step 2** Run phase2_add_tools.py to add the five public tools.

**Step 3** Run phase3_add_auth_tools.py to add authentication and booking tools.

**Step 4** Run phase4_add_seat_tools.py to add seat selection and upgrade tools.

**Step 5** Run phase5_add_supervisor.py to create Marco and link him to Sofia.

**Step 6** Run phase6_tune_prompt.py to improve Sofia's conversational tone.

**Step 7** Run phase7_fix_bugs.py to apply the tool call and language switching fixes.

**Step 8** Run patch_cancel_fix.py to patch the cancellation procedure.

**Step 9** Run step1_fix_eur_hallucination.py to fix the EUR hallucination bug and lower the temperature.

After running all steps, Sofia is fully configured and can be tested from the ElevenLabs dashboard. The agent dashboard link is printed at the end of each script.

---

## Important Notes

Never share your ElevenLabs API key publicly. Keep it in an environment variable or a local config file that is excluded from version control.

The agent_state.json file contains your live agent IDs. Keep this file locally and do not commit it to any public repository.

Each script is safe to re-run. Running a script again will overwrite the agent configuration with the same values, which is harmless.
