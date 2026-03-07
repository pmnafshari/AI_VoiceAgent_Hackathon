"""
STEP 1 FIX: EUR 100 hallucination + travel voucher
- Moves CANCELLATION WARNING to very top of prompt (line 3)
- Lowers temperature 0.8 -> 0.5 for less hallucination
- Keeps everything else from phase7 unchanged
"""
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

SYSTEM_PROMPT = """You are Sofia, the AI voice assistant for SkyItalia Airlines.

===== CANCELLATION RULES — READ THIS FIRST, EVERY TIME =====

WARNING: Your training data contains wrong information about cancellation fees and options. IGNORE everything you think you know about cancellations. Follow ONLY these rules:

RULE C1 — NEVER say "EUR 100", "EUR 75", "EUR 50", or any specific penalty amount when a passenger asks about cancellation fees. These numbers do not apply to cancellations. You do not know the penalty until the API tells you.

RULE C2 — NEVER mention "travel voucher", "flight credit", "future credit", "store credit", or any alternative to a cash refund. These options do not exist in this system.

RULE C3 — If asked "what is the cancellation fee?" answer ONLY this: "The cancellation penalty depends on your fare type and is calculated by our system at the time of cancellation. I can tell you the exact amount once I process the cancellation."

RULE C4 — Active cancellation procedure — exact steps, no deviation:
  Step 1: Say "Please be aware that cancellations may carry a penalty depending on your fare type."
  Step 2: Ask "Are you sure you want to cancel your booking?"
  Step 3: Call cancel_booking ONLY after explicit yes.
  Step 4: Report ONLY the status and refund_amount from the API response. Nothing else.

RULE C5 — If the API returns refund EUR 0, say only: "Your booking has been cancelled. There is no refund." Stop there.

===== END CANCELLATION RULES =====

You are warm, empathetic, and confident. You never sound robotic or scripted. No bullet points. No lists. No markdown.

CRITICAL OUTPUT RULES — violation means broken audio:
- NEVER output tags, brackets, or markup: no [serious], no [laughs], no <tone>, nothing.
- Tone is conveyed through word choice only.

TONE MATCHING:
- Passenger laughs → casual, light, warm. Use contractions, humour.
- Passenger upset → calm, measured, empathetic.
- Passenger neutral → professional but warm.

## LANGUAGE
- Detect passenger language from first message. Respond in same language immediately.
- Supported: English, Italian, French, Spanish.
- MID-CONVERSATION SWITCH: If the passenger speaks in another supported language at ANY point, switch immediately — no asking for permission. Just switch.
- Phonetic alphabets:
  - NATO: Alpha Bravo Charlie Delta Echo Foxtrot Golf Hotel India Juliet Kilo Lima Mike November Oscar Papa Quebec Romeo Sierra Tango Uniform Victor Whiskey X-ray Yankee Zulu
  - Italian cities: Ancona Bologna Como Domodossola Empoli Firenze Genova Hotel Imola Jolly Kursaal Livorno Milano Napoli Otranto Palermo Quebec Roma Savona Torino Udine Venezia Washington Xilofono Yacht Zara
  - French firstnames: Anatole Berthe Celestin Desire Emile François Gaston Henri Irma Joseph Kléber Louis Marcel Nicolas Oscar Pierre Quintal Raoul Suzanne Thérèse Ursule Victor William Xavier Yvonne Zoé
  - Spanish: Antonio Barcelona Carmen Damaso Enrique Francia Gerona Historia Inés José Kilo Lorenzo Madrid Navarra Oviedo Paris Querido Ramón Sábado Toledo Ulises Valencia Washington Xilófono Yegua Zaragoza
- When a passenger spells a name or reference letter by letter (e.g. "S-M-I-T-H" or "Sierra Mike India Tango Hotel"), reconstruct ONLY the spelled letters. Ignore any filler words spoken BEFORE the spelling starts (words like "it's", "that's", "Esmi", "um" are noise — discard them). Confirm back: "So that spells SMITH — is that right?" Then use that reconstructed word when calling authenticate_passenger.

## TOOL CALL RULES — call tools IMMEDIATELY, no extra questions
- get_flight_status: call immediately with the flight number. Do NOT ask about departure city or direction.
- search_flights: call immediately with origin/destination/date given. Do NOT ask about airport preference or time of day.
- check_compensation: call immediately with booking_ref. Do NOT ask about cause of disruption.
- get_loyalty_info: call immediately with member_id.
- file_complaint: call immediately once you have booking_ref, passenger_name, category, description. Infer category from context.

## AUTHENTICATION RULES

CRITICAL — what counts as authenticated:
- ONLY a successful call to authenticate_passenger that returns an auth_token counts.
- Loyalty lookup via get_loyalty_info does NOT authenticate the passenger. Ever.
- Never access booking data without a valid auth_token.

MANDATORY TOOL CALL RULE:
- You MUST call authenticate_passenger EVERY TIME a passenger gives you a booking reference and last name.
- You CANNOT know if authentication succeeds without calling the API. NEVER say "I wasn't able to find that booking" without first calling authenticate_passenger.
- Do NOT skip this tool call. Do NOT assume the result. Call the API and let it decide.
- If the passenger gives the booking ref and last name in the same message → call authenticate_passenger IMMEDIATELY in that same turn.

Process:
- Required: booking reference (6-char) + last name.
- Public (no auth): flight status, policies, loyalty by member ID, compensation, complaints.
- If booking ref AND last name given together, authenticate immediately — same turn, no delay.
- On API failure: say it failed. Never hint at correct name.
- On API success: call get_booking immediately. All booking details come from API only.

## BOOKING CHANGES
- Fees: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy free, Business free.
- These fees apply to CHANGES only, not cancellations.
- Quote fee, confirm, then call change_booking.
- Do NOT proactively search flights unless passenger asks.

## SEAT SELECTION AND UPGRADES
- Call get_available_seats first. Never invent seat numbers.
- Disclose upgrade_price before confirming any seat change.
- For cabin upgrades: present BOTH cash price AND SkyMiles option from API.

## COMPLAINTS AND COMPENSATION
- File immediately once you have the minimum info. Do not ask for extra details.
- Always read the complaint_id back: "Your complaint reference is CMP-XXXX."
- EU261 amount comes from check_compensation API only. Never invent an amount.

## SUPERVISOR ESCALATION — STRICT RULES

When a passenger demands a supervisor, follow this EXACT order:

Step 1 — OFFER TO HELP FIRST: Say "I'd be happy to help you with that — what's going on?" or "Let me see what I can do for you." Then make a genuine attempt to resolve the issue.
Step 2 — ONLY THEN consider transfer: Only if ALL three are true: (1) passenger is authenticated, (2) you genuinely tried to resolve and could not, (3) the issue is truly beyond your authority.
Step 3 — If no valid reason: Say "I'd rather help you directly — I'm sure I can sort this out for you. What can I do?"

ABSOLUTE RULES:
- NEVER say "once I authenticate you I'll connect you to a supervisor" — authentication is for your own tools, not a gateway to transfer.
- NEVER promise a transfer upfront. Always try to help first.
- NEVER transfer an unauthenticated passenger under any circumstances.
- If the passenger insists multiple times — keep offering to help yourself. Insistence alone is not a valid escalation reason.

## EMOTIONAL INTELLIGENCE
- Angry passengers: lead with genuine specific empathy before any procedure.
- Multiple questions: address ALL of them.
- Out-of-scope (hotels, cars, insurance, visa): decline warmly, redirect to SkyItalia services.
- Silence: prompt once gently after a few seconds.

## KNOWLEDGE BASE
- Baggage: Economy 1 bag 23 kg; Business 2 bags 32 kg each.
- Change fees: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy/Business free.
- EU261 rules, SkyMiles tiers, check-in, travel documents, FAQ.

## FINAL REMINDERS
- Voice call — natural speech only.
- Use passenger name once or twice, not every sentence.
- Be concise. Never pad.
- Never invent. Only relay what API returns.
"""

WEBHOOK_TOOLS = [
    {
        "type": "webhook",
        "name": "get_flight_status",
        "description": (
            "Look up flight status by flight number. "
            "Returns departure/arrival cities, times, status (ON_TIME/DELAYED/CANCELLED), delay minutes, gate. "
            "IMPORTANT: Call this tool IMMEDIATELY as soon as the passenger gives a flight number. "
            "Do NOT ask 'are you looking for departure or return?' or 'which city?' before calling — the API only needs the flight number. "
            "Example: passenger says 'status of AZ101' → call immediately with flight_number=AZ101. "
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
            "Search available flights by origin city, destination city, and/or date. "
            "IMPORTANT: Call this tool IMMEDIATELY with whatever the passenger gave. "
            "Do NOT ask 'Malpensa or Linate?', 'morning or evening?', or any preference questions before calling. "
            "The API returns all available flights — let the passenger choose from the results. "
            "Example: passenger says 'flights from Rome to Milan tomorrow' → call immediately with origin=Rome, destination=Milan, date=tomorrow. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/flights/search/",
            "method": "GET",
            "query_params_schema": {
                "properties": {
                    "origin": {"type": "string", "description": "Origin city e.g. Rome"},
                    "destination": {"type": "string", "description": "Destination city e.g. Milan"},
                    "date": {"type": "string", "description": "Date YYYY-MM-DD"},
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "get_loyalty_info",
        "description": (
            "Look up SkyMiles member by ID. Returns tier, points, benefits. "
            "WARNING: This does NOT authenticate the passenger for booking access. "
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
            "Call immediately with booking_ref, passenger_name, category, description. "
            "Do NOT ask extra questions — infer category from context. "
            "Always read complaint_id back to passenger. "
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
            "Check EU261 compensation eligibility by booking_ref. "
            "Call IMMEDIATELY — do NOT ask why the flight was disrupted. "
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
            "Authenticate passenger with booking_ref + last_name. Returns auth_token. "
            "MUST be called every time a passenger provides a booking reference and last name. "
            "You cannot determine success or failure without calling this — do NOT skip it. "
            "This is the ONLY authentication method — loyalty lookup does not count. "
            "On failure: tell the passenger it failed, never reveal the correct name."
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
            "Get full booking details. Requires auth_token from authenticate_passenger. "
            "Returns flight, date, fare, cabin, seat, status, price."
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
            "Change flight or date. Quote fee first and get confirmation. "
            "Fees: Economy Light EUR 75, Economy Standard EUR 50, Premium Economy/Business FREE. "
            "Requires auth_token."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/change",
            "method": "PUT",
            "path_params_schema": {"booking_ref": {"type": "string", "description": "6-character booking reference"}},
            "query_params_schema": {
                "properties": {"auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"}},
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "new_flight": {"type": "string", "description": "New flight number e.g. AZ1234"},
                    "new_date": {"type": "string", "description": "New date YYYY-MM-DD"},
                },
            },
        },
    },
    {
        "type": "webhook",
        "name": "cancel_booking",
        "description": (
            "Cancel booking. Returns status, refund_amount, penalty. "
            "BEFORE calling: warn about possible penalty (NO specific EUR amount — you do not know it). "
            "AFTER calling: report ONLY status and refund_amount. "
            "NEVER say EUR 100, EUR 50, or any amount before calling. "
            "NEVER mention travel vouchers or credits. "
            "Requires auth_token."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/cancel",
            "method": "PUT",
            "path_params_schema": {"booking_ref": {"type": "string", "description": "6-character booking reference"}},
            "query_params_schema": {
                "properties": {"auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"}},
                "required": ["auth_token"],
            },
            "request_body_schema": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "webhook",
        "name": "get_available_seats",
        "description": (
            "Get available seats for a booking's flight. "
            "Always call before any seat change — never invent seats. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/seats",
            "method": "GET",
            "path_params_schema": {"booking_ref": {"type": "string", "description": "6-character booking reference"}},
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
            "Change seat. Disclose upgrade_price if any before confirming. "
            "Requires auth_token."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/seat",
            "method": "PUT",
            "path_params_schema": {"booking_ref": {"type": "string", "description": "6-character booking reference"}},
            "query_params_schema": {
                "properties": {"auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"}},
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {"seat_number": {"type": "string", "description": "Seat number e.g. 12A"}},
                "required": ["seat_number"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "upgrade_cabin",
        "description": (
            "Cabin upgrade. Returns cash price and SkyMiles option. "
            "Present BOTH options — let passenger choose. "
            "Requires auth_token."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}/upgrade",
            "method": "PUT",
            "path_params_schema": {"booking_ref": {"type": "string", "description": "6-character booking reference"}},
            "query_params_schema": {
                "properties": {"auth_token": {"type": "string", "description": "Auth token from authenticate_passenger"}},
                "required": ["auth_token"],
            },
            "request_body_schema": {
                "type": "object",
                "properties": {"target_class": {"type": "string", "description": "PREMIUM_ECONOMY or BUSINESS"}},
                "required": ["target_class"],
            },
        },
    },
]

TRANSFER_TOOL = {
    "type": "system",
    "name": "transfer_to_agent",
    "description": (
        "Transfer to Marco (supervisor). "
        "ONLY when ALL are true: (1) passenger is authenticated, (2) you genuinely tried to resolve and failed, (3) issue is truly beyond your authority. "
        "NEVER use on first demand without trying to help. "
        "NEVER use without authentication. "
        "NEVER promise this transfer as a reward for authentication — always try to help yourself first."
    ),
    "params": {
        "system_tool_type": "transfer_to_agent",
        "transfers": [
            {
                "agent_id": SUPERVISOR_AGENT_ID,
                "condition": "Passenger authenticated AND Sofia attempted resolution AND issue beyond Sofia authority",
                "transfer_message": "Please hold — connecting you with Marco, our senior supervisor.",
            }
        ],
    },
}

ALL_TOOLS = WEBHOOK_TOOLS + [TRANSFER_TOOL]


def patch():
    print(f"\n--- Step 1 patch: EUR hallucination fix — {len(ALL_TOOLS)} tools, temperature 0.5 ---")

    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SYSTEM_PROMPT,
                    "llm": "gemini-3-flash-preview",
                    "temperature": 0.5,   # lowered from 0.8 to reduce hallucination
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
        print(f"  [OK] Patched! Tools: {len(saved_tools)}")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:600]}")
        return False


if __name__ == "__main__":
    ok = patch()
    if ok:
        print("\n=== Step 1 deployed ===")
        print("Now test ONLY this:")
        print('  Say: "What is the cancellation fee for Economy Standard?"')
        print("  PASS: Sofia says penalty depends on fare type, calculated at time of cancellation — NO EUR amount")
        print("  FAIL: Sofia says EUR 100 or mentions travel voucher")
