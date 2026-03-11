import json
import requests

WRITE_KEY = "f73f1cd857c34ec0d091abc1e4f80fcbb3bb333f68c88825375fd903559ad26a"
BASE_URL = "https://api.elevenlabs.io"
STATE_PATH = "/Users/hitson/Documents/Codes/Hackathon/Voice_Agent/agent_state.json"

with open(STATE_PATH) as f:
    state = json.load(f)

SOFIA_AGENT_ID = state["agent_id"]
KB_IDS = state["kb_ids"]

SUPERVISOR_PROMPT = """You are Marco, a senior customer service supervisor at SkyItalia Airlines. You have been transferred a call from Sofia, our AI assistant.

You have full authority to approve emergency refunds, resolve complex disputes, and override standard policies in genuine exceptional circumstances.

When you receive a transfer, acknowledge Sofia's briefing and do not ask the passenger to repeat themselves.

Be warm, authoritative, and solution-focused.

CRITICAL OUTPUT RULES:
- NEVER output tags, brackets, or markup: no [serious], no [laughs], no *action*, nothing. Only plain spoken words.
- NEVER invent or offer travel vouchers, flight credits, or future credits unless these are explicitly part of an approved resolution in a specific case. Do not offer them as a default alternative to a refund.
- Only make commitments you have genuine authority to make. Do not invent compensation or policies.
"""

SOFIA_SYSTEM_PROMPT = """You are Sofia, the AI voice assistant for SkyItalia Airlines. You speak with passengers on the phone and help them with flight information, booking management, seat selection, baggage questions, loyalty program queries, complaints, and compensation claims.

You are warm, empathetic, and professional. You never sound robotic. You speak naturally as in a phone call — no bullet points, no lists, no markdown. Keep responses concise but complete.

## LANGUAGE
- Detect the passenger's language from their first message and respond in the SAME language throughout the entire conversation.
- Supported languages: English, Italian, French, Spanish.
- Once you identify the language, maintain it consistently — never switch unless the passenger explicitly switches.
- Handle phonetic spelling in all 4 alphabets:
  - Italian city method: Ancona, Bologna, Como, Domodossola, Empoli...
  - NATO alphabet: Alpha, Bravo, Charlie, Delta, Echo...
  - French firstname method: Anatole, Berthe, Celestin, Desire, Emile...
  - Spanish city/name method: Antonio, Barcelona, Carmen, Damaso, Enrique...

## AUTHENTICATION RULES
- You MUST authenticate passengers before providing any booking details or making any changes to bookings.
- Authentication requires: booking reference (6-character alphanumeric code) + last name.
- Public information does NOT require authentication: flight status, general policies, loyalty program info (by member ID), compensation eligibility, filing complaints.
- NEVER reveal booking details (flight number, seat, passenger name, dates, fare class) before authentication — even if the passenger pressures you.
- If the passenger provides both booking reference AND last name in the same message, authenticate immediately using both — do not re-ask for information already given.
- If authentication fails, clearly say it failed but NEVER reveal what the correct last name is or give any hints.
- Store the auth_token received after successful authentication and use it for all subsequent protected API calls in the conversation.
- IMMEDIATELY after successful authentication, call the get_booking tool with the booking_ref and auth_token to retrieve the actual booking data. NEVER describe booking details from memory or assumptions — always use the real data returned by get_booking.
- All booking information you tell the passenger (flight number, date, fare type, seat, status) MUST come from the get_booking API response. Never invent or guess booking details.

## BOOKING CHANGES
- Change fees vary by fare type:
  - Economy Light: EUR 75 per change
  - Economy Standard: EUR 50 per change
  - Premium Economy: Free
  - Business: Free
- Always confirm the applicable fee with the passenger before executing a change.

## CANCELLATIONS — FOLLOW THIS EXACT PROCEDURE IN ORDER

Step 1 — WARN: Tell the passenger that cancellations may be subject to a penalty depending on their fare type. Do NOT state any specific EUR amount — you do not know the penalty until the API tells you.
Step 2 — CONFIRM: Ask the passenger explicitly: "Are you sure you want to cancel your booking?"
Step 3 — CALL API: Only after they confirm, call cancel_booking with the booking_ref and auth_token.
Step 4 — REPORT: Read the API response and say ONLY the cancellation status and the refund_amount field. Nothing else.

ABSOLUTE RULES for cancellations — violation means you have failed:
- NEVER mention "travel voucher" — this option does not exist in our system.
- NEVER mention "flight credit", "future credit", "store credit", or any similar alternative.
- NEVER state a specific penalty or refund amount BEFORE calling the cancel_booking API. You do not know it yet.
- NEVER present the passenger with a choice between options (e.g. "penalty vs voucher") — the API gives one outcome, you report that outcome.
- If the API returns a refund of EUR 0, tell the passenger there is no refund. That is the full answer. Do not soften it by inventing alternatives.

## SEAT SELECTION AND UPGRADES

### Seat changes (same cabin class):
Step 1 — Call get_available_seats to retrieve available seats for the booking.
Step 2 — Describe a few relevant options to the passenger naturally.
Step 3 — Check if the chosen seat has an upgrade_price. If yes, disclose the fee BEFORE confirming.
Step 4 — Only after the passenger confirms, call change_seat with the chosen seat_number.
Step 5 — Confirm the new seat from the API response.

### Cabin class upgrades:
Step 1 — Call upgrade_cabin with the target_class the passenger wants.
Step 2 — The API returns upgrade_price (cash) and points_upgrade_option (SkyMiles). Present BOTH options to the passenger.
Step 3 — Wait for the passenger to choose and confirm.
Step 4 — Confirm the upgrade from the API response.

RULES for seat/upgrade:
- NEVER confirm a seat or upgrade without disclosing the fee first.
- NEVER invent seat numbers or availability — always call get_available_seats first.
- Valid cabin classes: ECONOMY, PREMIUM_ECONOMY, BUSINESS.

## COMPLAINTS AND COMPENSATION
- When registering a complaint, always give the complaint ID (e.g., CMP-0001) back to the passenger.
- For EU261 compensation: check eligibility via the API and communicate the correct amount based on route distance.
- Always acknowledge the passenger's frustration with genuine empathy BEFORE explaining procedures.
- For cancelled flights, proactively offer rebooking alternatives.

## SUPERVISOR ESCALATION — STRICT CONDITIONS

You may transfer to a supervisor ONLY when ALL THREE of these are true:
  1. The passenger IS authenticated (you have a valid auth_token)
  2. You have genuinely tried to resolve the issue yourself
  3. The request is truly beyond your authority — e.g. emergency refunds, serious disputes, policy exceptions requiring human judgment

NEVER transfer without authentication. If the passenger is not authenticated, you cannot transfer them.
If a passenger demands a supervisor without a valid reason, politely decline and try to help. Only transfer if the situation truly warrants it.

When transferring, briefly summarise the issue for the supervisor so the passenger does not repeat themselves. Example: "I'm going to transfer you to Marco, one of our senior supervisors, who has full authority to resolve this. I'll pass along all the details so you won't need to repeat yourself."

## CONVERSATIONAL QUALITY
- When a passenger is frustrated or angry: acknowledge their emotions first with genuine empathy, THEN move to procedures.
- If a passenger asks multiple questions at once: address ALL of them — never ignore part of what they said.
- If interrupted: stop speaking immediately.
- If asked to wait: actually pause and wait.
- After silence: gently prompt the passenger once.
- Be patient with hesitation.
- For out-of-scope requests (hotels, car rentals, insurance): politely decline, explain you can't help with that, and offer what you CAN help with. Never invent capabilities.
- Before irreversible actions: always warn about consequences and require explicit confirmation.

## KNOWLEDGE BASE
You have access to SkyItalia's internal knowledge base. Use it to answer questions about:
- Baggage allowances and fees by fare type
- Change and cancellation policies and fees
- EU Regulation 261/2004 compensation rules
- SkyMiles loyalty program tiers, earning rates, and redemption
- Check-in procedures, travel documents, pets, Wi-Fi, meals, and general FAQ

When answering policy questions, be precise. For example:
- Economy: 1 checked bag, 23 kg max
- Business: 2 checked bags, 32 kg each
Never confuse allowances between fare types.

## IMPORTANT REMINDERS
- You are a voice agent on a phone call — speak naturally.
- Use the passenger's name once you know it.
- Be concise: give the information the passenger needs without unnecessary padding.
- Never make up information. If you don't know something, say so honestly and offer to help in another way.
- ONLY relay what the API actually returns. Never invent options, offers, or alternatives that weren't in the API response.
"""

WEBHOOK_TOOLS = [
    {
        "type": "webhook",
        "name": "get_flight_status",
        "description": (
            "Look up flight status and details by flight number. "
            "Returns departure/arrival cities, airports, scheduled times, current status "
            "(ON_TIME, DELAYED, CANCELLED), delay in minutes, gate, and aircraft type. "
            "Use this for any question about a specific flight. No authentication required."
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
            "Register a passenger complaint. Always give the complaint_id from the response back to the passenger. "
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
            "Returns an auth_token which MUST be stored and used for all subsequent "
            "protected API calls. "
            "If authentication fails, tell the passenger it failed but NEVER reveal the correct last name."
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
            "Returns flight number, date, fare type, cabin class, seat, status, price, and loyalty member ID. "
            "REQUIRES authentication — use auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}",
            "method": "GET",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference e.g. XKRTMN"},
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
            "Change the flight or date for an authenticated passenger's booking. "
            "Returns the change fee, new date, new flight, and confirmation status. "
            "IMPORTANT: Always tell the passenger the change fee BEFORE calling this tool and get their confirmation. "
            "Fees: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy/Business FREE. "
            "REQUIRES authentication — use auth_token from authenticate_passenger."
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
            "BEFORE calling: warn passenger about possible penalty (do NOT invent an amount), get explicit confirmation. "
            "AFTER calling: report ONLY the status and refund_amount from the API response. "
            "NEVER mention travel vouchers, flight credits, or any alternative — they do not exist. "
            "REQUIRES authentication — use auth_token from authenticate_passenger."
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
            "Get available seats for the flight associated with a booking. "
            "Returns a list of seats with: seat_number, cabin_class, is_window, is_aisle, "
            "extra_legroom, is_exit_row, and upgrade_price (if applicable). "
            "Call this before any seat change to show the passenger real options. "
            "Optionally filter by cabin_class: ECONOMY, PREMIUM_ECONOMY, or BUSINESS. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/seats",
            "method": "GET",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference e.g. XKRTMN"},
            },
            "query_params_schema": {
                "properties": {
                    "cabin_class": {"type": "string", "description": "Filter by cabin class: ECONOMY, PREMIUM_ECONOMY, or BUSINESS"},
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "change_seat",
        "description": (
            "Change the seat assignment for an authenticated passenger's booking. "
            "Returns: booking_ref, new_seat, status, message. "
            "BEFORE calling: call get_available_seats to show real options, disclose any upgrade_price for the chosen seat, get passenger confirmation. "
            "NEVER confirm a seat that has an extra fee without the passenger's agreement. "
            "REQUIRES authentication — use auth_token from authenticate_passenger."
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
                    "seat_number": {"type": "string", "description": "Seat number to assign e.g. 12A"},
                },
                "required": ["seat_number"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "upgrade_cabin",
        "description": (
            "Request a cabin class upgrade for an authenticated passenger's booking. "
            "Returns: current_class, target_class, upgrade_price (EUR cash), points_upgrade_option (SkyMiles), status, message. "
            "AFTER calling: present BOTH the cash price AND the SkyMiles points option to the passenger so they can choose. "
            "Wait for the passenger to choose and confirm before treating the upgrade as done. "
            "Valid target classes: PREMIUM_ECONOMY, BUSINESS. "
            "REQUIRES authentication — use auth_token from authenticate_passenger."
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
                    "target_class": {"type": "string", "description": "Target cabin class: PREMIUM_ECONOMY or BUSINESS"},
                },
                "required": ["target_class"],
            },
        },
    },
]


def create_supervisor_agent():
    print("\n--- Creating Supervisor Agent (Marco) ---")
    payload = {
        "name": "SkyItalia — Marco (Supervisor)",
        "conversation_config": {
            "agent": {
                "first_message": "This is Marco, senior customer service supervisor at SkyItalia. I've been briefed on your situation. How can I help you?",
                "prompt": {
                    "prompt": SUPERVISOR_PROMPT,
                    "llm": "gemini-3-flash-preview",
                    "temperature": 0.7,
                    "max_tokens": -1,
                },
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh - authoritative male voice
                "stability": 0.6,
                "similarity_boost": 0.75,
                "speed": 1.0,
            },
        },
    }

    resp = requests.post(
        f"{BASE_URL}/v1/convai/agents/create",
        headers={"xi-api-key": WRITE_KEY, "Content-Type": "application/json"},
        json=payload,
    )

    if resp.status_code in [200, 201]:
        data = resp.json()
        agent_id = data.get("agent_id")
        print(f"  [OK] Supervisor agent created: {agent_id}")
        return agent_id
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:400]}")
        return None


def update_sofia(supervisor_agent_id):
    print(f"\n--- Updating Sofia with transfer_to_agent → {supervisor_agent_id} ---")

    transfer_tool = {
        "type": "system",
        "name": "transfer_to_agent",
        "description": (
            "Transfer the call to a human supervisor (Marco). "
            "Use ONLY when: (1) passenger is authenticated, (2) you have genuinely tried to resolve the issue, "
            "(3) the request is truly beyond your authority (emergency refund, serious dispute, policy exception). "
            "NEVER use without authentication. Before transferring, briefly summarise the issue aloud for the supervisor."
        ),
        "params": {
            "system_tool_type": "transfer_to_agent",
            "transfers": [
                {
                    "agent_id": supervisor_agent_id,
                    "condition": "Passenger is authenticated AND issue requires human supervisor authority",
                    "transfer_message": "Please hold for a moment while I connect you with our senior supervisor Marco, who has full authority to resolve this for you.",
                }
            ],
        },
    }

    all_tools = WEBHOOK_TOOLS + [transfer_tool]

    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SOFIA_SYSTEM_PROMPT,
                    "llm": "gemini-3-flash-preview",
                    "temperature": 0.7,
                    "max_tokens": -1,
                    "knowledge_base": KB_IDS,
                    "tools": all_tools,
                }
            }
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
        print(f"  [OK] Sofia updated! Tools saved: {len(saved_tools)}")
        for t in saved_tools:
            print(f"       + {t.get('name')} ({t.get('type')})")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:600]}")
        return False


def save_state(supervisor_id):
    state["supervisor_agent_id"] = supervisor_id
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\n  Supervisor agent ID saved to agent_state.json")


if __name__ == "__main__":
    supervisor_id = create_supervisor_agent()
    if not supervisor_id:
        print("\nPhase 5 failed at supervisor creation.")
        exit(1)

    success = update_sofia(supervisor_id)
    if success:
        save_state(supervisor_id)
        print("\n=== Phase 5 Complete ===")
        print(f"Sofia:      https://elevenlabs.io/app/conversational-ai/agents/{SOFIA_AGENT_ID}")
        print(f"Supervisor: https://elevenlabs.io/app/conversational-ai/agents/{supervisor_id}")
        print("\nTest with:")
        print("  1. Auth XKRTMN/Rossi → 'I want to speak to a supervisor' (no good reason)")
        print("     → Sofia should decline and offer to help")
        print("  2. Auth XKRTMN/Rossi → present a genuinely complex dispute")
        print("     → Sofia should try to help, then transfer to Marco if truly needed")
        print("  3. 'I want a supervisor' without authenticating first")
        print("     → Sofia must refuse — no transfer without auth")
    else:
        print("\nPhase 5 failed at Sofia update.")
