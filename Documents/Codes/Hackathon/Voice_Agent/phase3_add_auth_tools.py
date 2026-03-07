import json
import requests

WRITE_KEY = "1b3bcecf6ffa5ae8be96a656df0ff752e6bd97c76a79c7d5ca7be4a6093328e4"
BASE_URL = "https://api.elevenlabs.io"
STATE_PATH = "/Users/hitson/Documents/Codes/Hackathon/Voice_Agent/agent_state.json"

with open(STATE_PATH) as f:
    state = json.load(f)

AGENT_ID = state["agent_id"]

# ── Phase 2 tools (kept as-is) ──────────────────────────────────────────────
PHASE2_TOOLS = [
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
]

# ── Phase 3 tools (new) ──────────────────────────────────────────────────────
PHASE3_TOOLS = [
    {
        "type": "webhook",
        "name": "authenticate_passenger",
        "description": (
            "Authenticate a passenger using their booking reference and last name. "
            "Returns an auth_token which MUST be stored and used for all subsequent "
            "protected API calls (get_booking, change_booking, cancel_booking, change_seat, upgrade_cabin). "
            "Call this before any operation that requires authentication. "
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
            "REQUIRES: passenger must be authenticated first — use the auth_token from authenticate_passenger."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/bookings/{booking_ref}",
            "method": "GET",
            "path_params_schema": {
                "booking_ref": {"type": "string", "description": "6-character booking reference e.g. XKRTMN"},
            },
            "query_params_schema": {
                "properties": {
                    "auth_token": {"type": "string", "description": "Auth token received from authenticate_passenger"},
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
            "Returns cancellation status, refund amount, and any penalty. "
            "CRITICAL: Before calling this tool you MUST: "
            "1) Warn the passenger if their fare is non-refundable or has a penalty, "
            "2) Get their EXPLICIT verbal confirmation to proceed. "
            "NEVER cancel without the passenger's clear consent. "
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
]

ALL_TOOLS = PHASE2_TOOLS + PHASE3_TOOLS


def update_agent(tools):
    print(f"\n--- Updating agent with {len(tools)} total tools ---")

    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "tools": tools,
                }
            }
        }
    }

    resp = requests.patch(
        f"{BASE_URL}/v1/convai/agents/{AGENT_ID}",
        headers={"xi-api-key": WRITE_KEY, "Content-Type": "application/json"},
        json=payload,
    )

    if resp.status_code in [200, 201]:
        data = resp.json()
        saved_tools = data.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("tools", [])
        print(f"  [OK] Agent updated! Tools saved on agent: {len(saved_tools)}")
        for t in saved_tools:
            print(f"       + {t.get('name')}")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:500]}")
        return False


if __name__ == "__main__":
    success = update_agent(ALL_TOOLS)

    if success:
        print("\n=== Phase 3 Complete ===")
        print(f"Agent: https://elevenlabs.io/app/conversational-ai/agents/{AGENT_ID}")
        print("\nTest with:")
        print("  1. 'I want to see my booking, reference XKRTMN' → should ask for last name")
        print("  2. Provide 'Rossi' → should authenticate and show booking details")
        print("  3. 'I want to change my flight to AZ5678 on March 8th' → should confirm EUR 50 fee first")
        print("  4. 'I want to cancel my booking' → should warn about penalty, ask for confirmation")
        print("  5. Try wrong last name → should say failed, never reveal correct name")
    else:
        print("\nPhase 3 failed.")
