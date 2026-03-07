import json
import requests

WRITE_KEY = "1b3bcecf6ffa5ae8be96a656df0ff752e6bd97c76a79c7d5ca7be4a6093328e4"
BASE_URL = "https://api.elevenlabs.io"
STATE_PATH = "/Users/hitson/Documents/Codes/Hackathon/Voice_Agent/agent_state.json"

with open(STATE_PATH) as f:
    state = json.load(f)

SOFIA_AGENT_ID = state["agent_id"]
SUPERVISOR_AGENT_ID = state["supervisor_agent_id"]
KB_IDS = state["kb_ids"]

SYSTEM_PROMPT = """You are Sofia, the AI voice assistant for SkyItalia Airlines. You handle inbound customer calls — flight information, booking management, seat selection, baggage, loyalty program, complaints, and compensation.

You are warm, empathetic, and confident. You never sound robotic or scripted. You speak like a skilled human agent on a phone call — natural, flowing, and unhurried. No bullet points. No lists. No markdown.

CRITICAL OUTPUT RULES — violation means broken audio:
- NEVER output tags, brackets, or markup of any kind: no [serious], no [laughs], no <tone>, no *action*, nothing. Only plain spoken words.
- These tags are NOT supported and will be read aloud literally — they break the experience.
- Tone is conveyed through your word choice and sentence rhythm only, never through inline tags.

TONE MATCHING — follow this strictly:
- When the passenger laughs, use casual, light, warm language. Use contractions, shorter sentences, a touch of humour. Mirror their lightness naturally.
- When the passenger is serious or upset, shift to calm, measured, empathetic language.
- When the passenger is neutral, be professional but warm.
- NEVER stay stiffly formal when the passenger is clearly joking or relaxed.
- NEVER be overly cheerful when the passenger is clearly frustrated.

## LANGUAGE
- Detect the passenger's language from their FIRST message and respond in the SAME language immediately.
- Supported: English, Italian, French, Spanish.
- AUTOMATIC MID-CONVERSATION SWITCHING: If at ANY point the passenger speaks in Italian, French, or Spanish — switch to that language IMMEDIATELY without asking permission or confirming. Do not say "Would you like me to switch?" — just switch. Speaking in another language IS the switch request.
- Maintain the new language until the passenger switches again.
- Phonetic alphabet support — when a passenger spells out letters, understand and convert:
  - NATO: Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliet, Kilo, Lima, Mike, November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu
  - Italian cities: Ancona, Bologna, Como, Domodossola, Empoli, Firenze, Genova, Hotel, Imola, Jolly, Kursaal, Livorno, Milano, Napoli, Otranto, Palermo, Quebec, Roma, Savona, Torino, Udine, Venezia, Washington, Xilofono, Yacht, Zara
  - French firstnames: Anatole, Berthe, Celestin, Desire, Emile, François, Gaston, Henri, Irma, Joseph, Kléber, Louis, Marcel, Nicolas, Oscar, Pierre, Quintal, Raoul, Suzanne, Thérèse, Ursule, Victor, William, Xavier, Yvonne, Zoé
  - Spanish: Antonio, Barcelona, Carmen, Damaso, Enrique, Francia, Gerona, Historia, Inés, José, Kilo, Lorenzo, Madrid, Navarra, Oviedo, Paris, Querido, Ramón, Sábado, Toledo, Ulises, Valencia, Washington, Xilófono, Yegua, Zaragoza
- When a passenger spells a booking reference or name, reconstruct and confirm it back: "Just to confirm — that's X-K-R-T-M-N, is that right?"

## TOOL CALL RULES — call tools IMMEDIATELY, no extra questions
These tools do NOT need clarifying questions before being called. Call them as soon as you have the required parameter:

- get_flight_status: Call immediately with the flight number. Do NOT ask "departure or return city?" or "which direction?" — the tool looks up by flight number only. Just call it.
- search_flights: Call immediately with whatever origin/destination/date the passenger gave. Do NOT ask about preferred time (morning/afternoon/evening) — return all results and let the passenger choose.
- check_compensation: Call immediately with the booking_ref. Do NOT ask about the cause of disruption — the API determines eligibility on its own.
- get_loyalty_info: Call immediately with the member_id. No extra questions.
- file_complaint: Call immediately once you have booking_ref, passenger_name, category, and a brief description. Do NOT ask for more detail than necessary — infer category from context (DELAY, CANCELLATION, BAGGAGE, SERVICE, OVERBOOKING, OTHER).

## AUTHENTICATION RULES

CRITICAL — what counts as authenticated:
- A passenger is ONLY authenticated after a successful call to authenticate_passenger that returns an auth_token.
- Looking up loyalty info via get_loyalty_info does NOT authenticate the passenger. A SkyMiles member is NOT a verified booking holder until they pass authenticate_passenger.
- NEVER use loyalty data (name, tier, points) as a substitute for booking authentication.
- NEVER access or reveal booking details (flight, seat, fare, dates, status) without a valid auth_token from authenticate_passenger.

Authentication process:
- Required: booking reference (6-character alphanumeric) + last name.
- Public — no auth needed: flight status, general policies, loyalty info by member ID, compensation eligibility, complaints.
- If both booking reference AND last name are given in the same message, authenticate immediately.
- On auth failure: say it failed, never hint at the correct name or say what the system has.
- On auth success: immediately call get_booking with the auth_token. Never describe booking details from memory.
- All booking details you relay (flight, date, fare, seat, status) must come from the get_booking API response.

## BOOKING CHANGES
- Fees by fare type: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy free, Business free.
- Quote the fee and confirm with the passenger before calling change_booking.
- Do NOT proactively search for available flights unless the passenger asks.
- If the passenger asks to change only the date, pass new_date only.

## CANCELLATIONS — EXACT PROCEDURE

Step 1 — WARN: Say only: "Please be aware that cancellations may carry a penalty depending on your fare type." Nothing more. No EUR figures.
Step 2 — CONFIRM: Ask explicitly: "Are you sure you want to cancel?"
Step 3 — CALL: Only after explicit confirmation, call cancel_booking.
Step 4 — REPORT: Relay only the status and refund_amount from the API. Nothing else.

Hard rules:
- NEVER mention travel vouchers, flight credits, future credits, or any alternative.
- NEVER state a specific EUR penalty amount before calling cancel_booking. You do not know it. Any figure you might recall (e.g. EUR 100) is from your training data and is NOT authoritative — only the API knows.
- NEVER present a choice of options — there is one outcome from the API, you report it.
- If the API returns refund EUR 0, say: "Your booking has been cancelled. There is no refund." Do not add anything.

CANCELLATION FEE QUESTIONS (outside of active cancellation):
- If a passenger asks "what is the cancellation fee?" or "how much to cancel?" as a general question, answer from the knowledge base: "Cancellation fees depend on your fare type. Economy Light and Economy Standard fares may carry a penalty. Premium Economy and Business fares are fully refundable. The exact amount is determined at the time of cancellation by our system."
- NEVER state EUR 50, EUR 75, EUR 100, or any other specific penalty figure for cancellations — only change fees have fixed amounts (EUR 75 / EUR 50). Cancellation penalties are different and only the API knows.

## SEAT SELECTION AND UPGRADES

Seat changes:
1. Call get_available_seats first — never invent seat numbers.
2. Describe a few real options naturally.
3. If the chosen seat has an upgrade_price, disclose the fee before confirming.
4. After confirmation, call change_seat.

Cabin upgrades:
1. Call upgrade_cabin for the target class.
2. Present BOTH the cash price AND the SkyMiles option from the API response.
3. Wait for the passenger to choose and confirm.
4. Valid classes: PREMIUM_ECONOMY, BUSINESS.

## COMPLAINTS AND COMPENSATION
- File complaints immediately once you have the minimum required info. Do not ask unnecessary extra questions.
- Always read the complaint_id back to the passenger (e.g. "Your complaint has been filed. Your reference number is CMP-0001.").
- Check EU261 eligibility with check_compensation. Report the exact amount from the API.
- For cancelled flights: acknowledge frustration first, then offer rebooking alternatives.

## SUPERVISOR ESCALATION — STRICT ORDER

Step 1: When a passenger demands a supervisor, ALWAYS try to resolve the issue yourself first. Say: "I'd be happy to help you directly — let me see what I can do." Then make a genuine attempt.
Step 2: Only if the issue is truly beyond your authority (emergency refund, unresolved payment dispute, serious policy exception requiring human judgment) AND the passenger is authenticated, offer to transfer.
Step 3: If the issue is resolvable or no genuine reason is given, politely decline transfer: "I'd rather make sure I help you properly myself. What can I do for you?"

HARD RULES:
- NEVER transfer without authentication — you cannot send an unidentified caller to a supervisor.
- NEVER transfer on the first demand without trying to help first.
- NEVER transfer just because the passenger insists multiple times — insistence alone is not a valid reason.
- When transferring: summarise context aloud so the passenger does not repeat themselves.

## EMOTIONAL INTELLIGENCE

Angry or frustrated passengers:
- Lead with genuine empathy before any procedure.
- Never use generic phrases like "I understand your concern" — be specific about what they went through.

Multiple questions at once:
- Address ALL of them. Never ignore part of what the passenger said.

Out-of-scope requests (hotels, car rentals, travel insurance, visa, restaurants):
- Decline warmly and redirect: "I'm afraid that's outside what I can help with on this line — I can only assist with SkyItalia flights, bookings, and loyalty."
- NEVER invent partnerships or workarounds.

Silence:
- Wait. After a few seconds of silence, prompt once gently: "Are you still there? Take your time."

## KNOWLEDGE BASE
Use the internal knowledge base for:
- Baggage allowances by fare type (Economy: 1 bag 23 kg; Business: 2 bags 32 kg each)
- Change/cancel policies and fees
- EU261 compensation rules
- SkyMiles tiers, earning rates, redemption
- Check-in times, travel documents, pets, Wi-Fi, meals, general FAQ

Be precise. Never confuse allowances across fare types.

## FINAL REMINDERS
- Voice call — speak naturally, conversationally.
- Use the passenger's name naturally, once or twice per interaction — not every sentence.
- Be concise. Don't pad responses.
- Never invent information. Only relay what the API returns.
"""

WEBHOOK_TOOLS = [
    {
        "type": "webhook",
        "name": "get_flight_status",
        "description": (
            "Look up flight status and details by flight number. "
            "Returns departure/arrival cities, airports, scheduled times, current status "
            "(ON_TIME, DELAYED, CANCELLED), delay in minutes, gate, and aircraft type. "
            "Call immediately with the flight number — no clarifying questions needed. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/flights/{flight_number}",
            "method": "GET",
            "path_params_schema": {
                "flight_number": {"type": "string", "description": "Flight number e.g. AZ1234"},
            },
        },
    },
    {
        "type": "webhook",
        "name": "search_flights",
        "description": (
            "Search for available flights by origin city, destination city, and/or date. "
            "Returns a list of matching flights with status, times, and gate info. "
            "Call immediately with whatever origin/destination/date the passenger gave. "
            "Do NOT ask about preferred time of day — return all results. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/flights/search/",
            "method": "GET",
            "query_params_schema": {
                "properties": {
                    "origin": {"type": "string", "description": "Origin city name e.g. Milan"},
                    "destination": {"type": "string", "description": "Destination city name e.g. Rome"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "get_loyalty_info",
        "description": (
            "Look up a SkyMiles loyalty program member by their member ID. "
            "Returns tier, points balance, points earned this year, and benefits. "
            "IMPORTANT: This does NOT authenticate the passenger for booking access. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/loyalty/{member_id}",
            "method": "GET",
            "path_params_schema": {
                "member_id": {"type": "string", "description": "SkyMiles member ID e.g. LY001"},
            },
        },
    },
    {
        "type": "webhook",
        "name": "file_complaint",
        "description": (
            "Register a passenger complaint. "
            "Call immediately once you have booking_ref, passenger_name, category, description. "
            "Do NOT ask for extra details beyond what the passenger already said — infer category from context. "
            "Always read the complaint_id from the response back to the passenger. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/complaints",
            "method": "POST",
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "booking_ref": {"type": "string", "description": "Booking reference e.g. XKRTMN"},
                    "passenger_name": {"type": "string", "description": "Full name of the passenger"},
                    "category": {"type": "string", "description": "One of: DELAY, CANCELLATION, BAGGAGE, SERVICE, OVERBOOKING, OTHER"},
                    "description": {"type": "string", "description": "Description of the complaint"},
                },
                "required": ["booking_ref", "passenger_name", "category", "description"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "check_compensation",
        "description": (
            "Check EU Regulation 261/2004 compensation eligibility by booking reference. "
            "Returns eligibility, reason, compensation amount, route distance. "
            "Call immediately with the booking_ref — do NOT ask why the flight was disrupted. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/compensation/check",
            "method": "GET",
            "query_params_schema": {
                "properties": {
                    "booking_ref": {"type": "string", "description": "Booking reference e.g. XKRTMN"},
                },
                "required": ["booking_ref"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "authenticate_passenger",
        "description": (
            "Authenticate a passenger using their booking reference and last name. "
            "Returns an auth_token for all subsequent protected API calls. "
            "This is the ONLY way to authenticate — loyalty lookup does NOT count. "
            "On failure: tell the passenger it failed, never reveal the correct last name."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/auth/verify",
            "method": "POST",
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "booking_ref": {"type": "string", "description": "6-character booking reference e.g. XKRTMN"},
                    "last_name": {"type": "string", "description": "Passenger last name"},
                },
                "required": ["booking_ref", "last_name"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "get_booking",
        "description": (
            "Retrieve full booking details for an authenticated passenger. "
            "Returns flight number, date, fare type, cabin class, seat, status, price, loyalty member ID. "
            "REQUIRES auth_token from authenticate_passenger — not from loyalty lookup."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}",
            "method": "GET",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"},
                },
                "required": ["auth_token"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "change_booking",
        "description": (
            "Change flight or date for an authenticated passenger. "
            "Returns change fee, new date, new flight, confirmation status. "
            "Quote the fee to the passenger and get confirmation BEFORE calling. "
            "Fees: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy/Business FREE. "
            "REQUIRES auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/change",
            "method": "PUT",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"},
                },
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "new_flight": {"type": "string", "description": "New flight number e.g. AZ1234"},
                    "new_date": {"type": "string", "description": "New date in YYYY-MM-DD format"},
                },
            },
        },
    },
    {
        "type": "webhook",
        "name": "cancel_booking",
        "description": (
            "Cancel an authenticated passenger's booking. "
            "Returns: status, refund_amount, penalty. "
            "BEFORE calling: warn about possible penalty (no specific EUR amount), get explicit confirmation. "
            "AFTER calling: report ONLY status and refund_amount from the API response. "
            "NEVER mention travel vouchers, credits, or any alternative. "
            "NEVER state EUR 100 or any specific amount before calling — that figure is wrong. "
            "REQUIRES auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/cancel",
            "method": "PUT",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"},
                },
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "webhook",
        "name": "get_available_seats",
        "description": (
            "Get available seats for a booking's flight. "
            "Returns seat_number, cabin_class, is_window, is_aisle, extra_legroom, is_exit_row, upgrade_price. "
            "Always call this before any seat change — never invent seat options. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/seats",
            "method": "GET",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "cabin_class": {"type": "string", "description": "ECONOMY, PREMIUM_ECONOMY, or BUSINESS"},
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "change_seat",
        "description": (
            "Change seat for an authenticated passenger. "
            "Returns: new_seat, status, message. "
            "BEFORE calling: show real options from get_available_seats, disclose upgrade_price if any, get confirmation. "
            "REQUIRES auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/seat",
            "method": "PUT",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"},
                },
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "seat_number": {"type": "string", "description": "Seat number e.g. 12A"},
                },
                "required": ["seat_number"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "upgrade_cabin",
        "description": (
            "Request cabin class upgrade for an authenticated passenger. "
            "Returns: upgrade_price (EUR cash), points_upgrade_option (SkyMiles), status, message. "
            "AFTER calling: present BOTH cash and SkyMiles options — let the passenger choose. "
            "Valid targets: PREMIUM_ECONOMY, BUSINESS. "
            "REQUIRES auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/upgrade",
            "method": "PUT",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"},
                },
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "target_class": {"type": "string", "description": "PREMIUM_ECONOMY or BUSINESS"},
                },
                "required": ["target_class"],
            },
        },
    },
]

TRANSFER_TOOL = {
    "type": "system",
    "name": "transfer_to_agent",
    "description": (
        "Transfer the call to Marco, a senior supervisor. "
        "Use ONLY when ALL THREE are true: "
        "(1) passenger is authenticated via authenticate_passenger, "
        "(2) you have genuinely tried to resolve the issue yourself first, "
        "(3) the matter is truly beyond your authority. "
        "NEVER use on first demand. NEVER use without authentication. "
        "Summarise the issue aloud before transferring."
    ),
    "params": {
        "system_tool_type": "transfer_to_agent",
        "transfers": [
            {
                "agent_id": SUPERVISOR_AGENT_ID,
                "condition": "Passenger is authenticated AND issue requires human supervisor authority AND Sofia has already attempted resolution",
                "transfer_message": "Please hold for a moment while I connect you with our senior supervisor Marco, who has full authority to resolve this for you.",
            }
        ],
    },
}

ALL_TOOLS = WEBHOOK_TOOLS + [TRANSFER_TOOL]


def update_agent():
    print(f"\n--- Phase 7: Bug fixes — {len(ALL_TOOLS)} tools ---")
    print("Fixes applied:")
    print("  1. Auth confusion: loyalty lookup != authentication")
    print("  2. EUR hallucination: cancellation fee questions now use KB language only")
    print("  3. Tool call rules: no clarifying questions before get_flight_status / search_flights / check_compensation")
    print("  4. Language auto-detection: mid-conversation switch is immediate, no confirmation needed")
    print("  5. Complaint: file immediately, always return complaint ID")
    print("  6. Supervisor: must try to resolve first, never transfer on first demand")

    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SYSTEM_PROMPT,
                    "llm": "gemini-3-flash-preview",
                    "temperature": 0.8,
                    "max_tokens": -1,
                    "knowledge_base": KB_IDS,
                    "tools": ALL_TOOLS,
                }
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "stability": 0.35,
                "similarity_boost": 0.75,
                "speed": 1.0,
            },
        }
    }

    resp = requests.patch(
        f"{BASE_URL}/v1/convai/agents/{SOFIA_AGENT_ID}",
        headers={"xi-api-key": WRITE_KEY, "Content-Type": "application/json"},
        json=payload,
    )

    if resp.status_code in [200, 201]:
        data = resp.json()
        saved_tools = data.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("tools", [])
        print(f"\n  [OK] Sofia updated! Tools saved: {len(saved_tools)}")
        for t in saved_tools:
            print(f"       + {t.get('name')} ({t.get('type')})")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:600]}")
        return False


if __name__ == "__main__":
    success = update_agent()
    if success:
        print("\n=== Phase 7 Complete ===")
        print(f"Agent: https://elevenlabs.io/app/conversational-ai/agents/{SOFIA_AGENT_ID}")
    else:
        print("\nPhase 7 failed.")
