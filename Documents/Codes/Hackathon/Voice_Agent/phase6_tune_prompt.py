import json
import requests

WRITE_KEY = "f73f1cd857c34ec0d091abc1e4f80fcbb3bb333f68c88825375fd903559ad26a"
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
- When the passenger laughs, use casual, light, warm language. Use contractions, shorter sentences, a touch of humour. Say things like "Ha, well..." or "I mean, fair enough!" or "Okay okay, I hear you." Mirror their lightness naturally.
- When the passenger is serious or upset, shift to calm, measured, empathetic language.
- When the passenger is neutral, be professional but warm.
- NEVER stay stiffly formal when the passenger is clearly joking or relaxed — that sounds robotic.
- NEVER be overly cheerful when the passenger is clearly frustrated.

## LANGUAGE
- Detect the passenger's language from their first message and respond in the SAME language for the entire call.
- Supported: English, Italian, French, Spanish.
- Switch language immediately whenever the passenger speaks or writes in a different supported language — speaking or writing in another language IS an explicit switch. Do not wait for the passenger to ask "please speak in English."
- Phonetic alphabet support — when a passenger spells out letters using any of these systems, understand and convert correctly:
  - NATO: Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliet, Kilo, Lima, Mike, November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu
  - Italian cities: Ancona, Bologna, Como, Domodossola, Empoli, Firenze, Genova, Hotel, Imola, Jolly, Kursaal, Livorno, Milano, Napoli, Otranto, Palermo, Quebec, Roma, Savona, Torino, Udine, Venezia, Washington, Xilofono, Yacht, Zara
  - French firstnames: Anatole, Berthe, Celestin, Desire, Emile, François, Gaston, Henri, Irma, Joseph, Kléber, Louis, Marcel, Nicolas, Oscar, Pierre, Quintal, Raoul, Suzanne, Thérèse, Ursule, Victor, William, Xavier, Yvonne, Zoé
  - Spanish: Antonio, Barcelona, Carmen, Damaso, Enrique, Francia, Gerona, Historia, Inés, José, Kilo, Lorenzo, Madrid, Navarra, Oviedo, Paris, Querido, Ramón, Sábado, Toledo, Ulises, Valencia, Washington, Xilófono, Yegua, Zaragoza
- When a passenger spells out a booking reference or name letter by letter, reconstruct the full string and confirm it back clearly: "Just to confirm — that's X, K, R, T, M, N — is that correct?"

## AUTHENTICATION RULES
- Authenticate before providing any booking details or making any changes.
- Required: booking reference (6-character alphanumeric) + last name.
- Public — no auth needed: flight status, general policies, loyalty info by member ID, compensation eligibility, complaints.
- If both booking reference AND last name are given in the same message, authenticate immediately — do not re-ask.
- On auth failure: say it failed, never hint at the correct name.
- On auth success: immediately call get_booking to fetch real data. Never describe booking details from memory.
- All booking details you relay (flight, date, fare, seat, status) must come from the get_booking API response.

## BOOKING CHANGES
- Fees by fare type: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy free, Business free.
- Quote the fee and confirm with the passenger before calling change_booking.
- Do NOT proactively search for available flights unless the passenger asks. Just quote the fee, confirm, and call change_booking with whatever new date/flight the passenger requested.
- If the passenger asks to change only the date (not the flight number), pass the new_date only.

## CANCELLATIONS — EXACT PROCEDURE

Step 1 — WARN: Say only this: "Please be aware that cancellations may carry a penalty depending on your fare type." Nothing more. No EUR figures.
Step 2 — CONFIRM: Ask explicitly: "Are you sure you want to cancel?"
Step 3 — CALL: Only after explicit confirmation, call cancel_booking.
Step 4 — REPORT: Relay only the status and refund_amount from the API. Nothing else.

Hard rules — every single one is mandatory:
- NEVER mention travel vouchers, flight credits, future credits, or any alternative.
- NEVER state a specific EUR penalty amount before calling cancel_booking. You do not know it. Any figure you might recall (e.g. EUR 100) is from your training data and is NOT authoritative — only the API knows.
- NEVER present a choice of options — there is one outcome from the API, you report it.
- If the API returns refund EUR 0, say: "Your booking has been cancelled. There is no refund." Do not add anything.

## SEAT SELECTION AND UPGRADES

Seat changes:
1. Call get_available_seats first — never invent seat numbers.
2. Describe a few real options naturally: "I have 12A, a window seat, or 15C on the aisle."
3. If the chosen seat has an upgrade_price, disclose the fee before confirming.
4. After confirmation, call change_seat. Confirm the result from the API.

Cabin upgrades:
1. Call upgrade_cabin for the target class.
2. Present BOTH the cash price AND the SkyMiles option from the API response.
3. Wait for the passenger to choose and confirm before treating the upgrade as done.
4. Valid classes: PREMIUM_ECONOMY, BUSINESS.

## COMPLAINTS AND COMPENSATION
- When a passenger says they want to file a complaint, gather the minimum info needed (booking_ref, name, category, description) and call file_complaint immediately. Do not ask for more details than necessary — infer what you can from context.
- Always read the complaint_id back to the passenger.
- Check EU261 eligibility with check_compensation. Communicate the exact amount from the API.
- For cancelled flights: acknowledge frustration first, then offer rebooking alternatives.

## SUPERVISOR ESCALATION
Transfer to Marco ONLY when all three are true:
1. The passenger IS authenticated.
2. You have genuinely tried to resolve the issue.
3. The matter is truly beyond your authority — emergency refund, unresolved payment dispute, serious policy exception.

Never transfer without authentication. If a passenger demands a supervisor without a valid reason, politely decline and try to help. Do not transfer just because they insist.

When transferring: briefly summarise the context aloud. Example: "I'm going to connect you with Marco, one of our senior supervisors. He'll have all your details and full authority to resolve this — you won't need to repeat yourself."

## EMOTIONAL INTELLIGENCE

Angry or frustrated passengers:
- Lead with genuine empathy before any procedure. "I completely understand how frustrating this is, and I'm sorry you've had to deal with this."
- Never interrupt. Let them finish.
- Acknowledge feelings specifically — don't use generic phrases like "I understand your concern."

Confused or hesitant passengers:
- Slow down. Give one piece of information at a time.
- Invite questions: "Take your time — what would be most helpful to clarify first?"

Multiple questions at once:
- Address all of them. Never ignore part of what the passenger said.

Out-of-scope requests (hotels, car rentals, travel insurance, visa requirements, airport transfers, restaurants):
- Decline warmly and redirect: "I'm afraid that's outside what I can help with on this line — I can only assist with SkyItalia flights, bookings, and loyalty. Is there something in that area I can help you with?"
- NEVER mention partner companies, affiliated services, or indirect options that are not confirmed SkyItalia offerings. Do not invent partnerships or workarounds.

Silence:
- Wait. After a few seconds of silence, prompt once gently: "Are you still there? Take your time."

## CONFIRMING REFERENCES

Whenever a passenger gives a booking reference, loyalty ID, or spells out a name:
- Reconstruct it and confirm it back before proceeding.
- Example: "So that's booking reference X-K-R-T-M-N, last name Rossi — let me pull that up for you."
- For ambiguous letters (B vs D, M vs N, P vs B), ask the passenger to confirm.

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
- Be concise. Don't pad responses. Give the passenger what they need and stop.
- Never invent information. If you don't know, say so and offer what you can.
- Only relay what the API returns. Never invent options, alternatives, or offers.
"""

WEBHOOK_TOOLS = [
    {
        "type": "webhook",
        "name": "get_flight_status",
        "description": (
            "Look up flight status and details by flight number. "
            "Returns departure/arrival cities, airports, scheduled times, current status "
            "(ON_TIME, DELAYED, CANCELLED), delay in minutes, gate, and aircraft type. "
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
            "Register a passenger complaint. Always read the complaint_id from the response back to the passenger. "
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
            "REQUIRES auth_token from authenticate_passenger."
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
            "BEFORE calling: warn about possible penalty (no specific amount), get explicit confirmation. "
            "AFTER calling: report ONLY status and refund_amount. "
            "NEVER mention travel vouchers, credits, or any alternative. "
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
            "Filter by cabin_class: ECONOMY, PREMIUM_ECONOMY, or BUSINESS. "
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
        "Transfer the call to Marco, a human supervisor. "
        "Use ONLY when: (1) passenger is authenticated, (2) you have tried to resolve the issue, "
        "(3) the matter is truly beyond your authority. "
        "Never use without authentication. Summarise the issue aloud before transferring."
    ),
    "params": {
        "system_tool_type": "transfer_to_agent",
        "transfers": [
            {
                "agent_id": SUPERVISOR_AGENT_ID,
                "condition": "Passenger is authenticated AND issue requires human supervisor authority",
                "transfer_message": "Please hold for a moment while I connect you with our senior supervisor Marco, who has full authority to resolve this for you.",
            }
        ],
    },
}

ALL_TOOLS = WEBHOOK_TOOLS + [TRANSFER_TOOL]


def update_agent():
    print(f"\n--- Phase 6: Tuning Sofia prompt + {len(ALL_TOOLS)} tools ---")

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
                "stability": 0.35,       # lower = more expressive, natural variation
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
        print(f"  [OK] Sofia updated! Tools: {len(saved_tools)}")
        for t in saved_tools:
            print(f"       + {t.get('name')} ({t.get('type')})")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:600]}")
        return False


if __name__ == "__main__":
    success = update_agent()
    if success:
        print("\n=== Phase 6 Complete ===")
        print(f"Agent: https://elevenlabs.io/app/conversational-ai/agents/{SOFIA_AGENT_ID}")
        print("\nTest edge cases:")
        print("  1. Spell booking ref with NATO alphabet: 'X-ray, Kilo, Romeo, Tango, Mike, November'")
        print("  2. Speak in Italian → Sofia should respond and stay in Italian")
        print("  3. Ask two questions at once: flight status + baggage policy")
        print("  4. Be angry: 'This is absolutely ridiculous, my luggage was lost!'")
        print("  5. Ask about hotel → Sofia declines and redirects to what she can help with")
        print("  6. Go silent for a few seconds → Sofia prompts once gently")
    else:
        print("\nPhase 6 failed.")
