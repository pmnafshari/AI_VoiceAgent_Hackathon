import json
import requests

WRITE_KEY = "1b3bcecf6ffa5ae8be96a656df0ff752e6bd97c76a79c7d5ca7be4a6093328e4"
BASE_URL = "https://api.elevenlabs.io"
STATE_PATH = "/Users/hitson/Documents/Codes/Hackathon/Voice_Agent/agent_state.json"

# Load agent_id from Phase 1
with open(STATE_PATH) as f:
    state = json.load(f)

AGENT_ID = state["agent_id"]
KB_IDS = state["kb_ids"]

PUBLIC_TOOLS = [
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
                "flight_number": {
                    "type": "string",
                    "description": "The flight number to look up, e.g. AZ1234",
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "search_flights",
        "description": (
            "Search for available flights by origin city, destination city, and/or date. "
            "Returns a list of matching flights with status, times, and gate info. "
            "Use this when the passenger wants to find flights on a route or date. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/flights/search/",
            "method": "GET",
            "query_params_schema": {
                "properties": {
                    "origin": {"type": "string", "description": "Origin city name, e.g. Milan"},
                    "destination": {"type": "string", "description": "Destination city name, e.g. Rome"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format, e.g. 2026-03-08"},
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "get_loyalty_info",
        "description": (
            "Look up a SkyMiles loyalty program member by their member ID. "
            "Returns the member's name, tier (SILVER/GOLD/PLATINUM), points balance, "
            "points earned this year, tier status, and full list of benefits. "
            "No authentication required — only the member ID is needed."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/loyalty/{member_id}",
            "method": "GET",
            "path_params_schema": {
                "member_id": {
                    "type": "string",
                    "description": "The SkyMiles member ID, e.g. LY001",
                }
            },
        },
    },
    {
        "type": "webhook",
        "name": "file_complaint",
        "description": (
            "Register a passenger complaint and receive a complaint ID. "
            "Use this when the passenger wants to formally file a complaint about a flight, "
            "delay, cancellation, baggage issue, service quality, or overbooking. "
            "Always read the complaint_id from the response and give it to the passenger. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/complaints",
            "method": "POST",
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "booking_ref": {"type": "string", "description": "Passenger booking reference e.g. XKRTMN"},
                    "passenger_name": {"type": "string", "description": "Full name of the passenger"},
                    "category": {
                        "type": "string",
                        "description": "Must be exactly one of: DELAY, CANCELLATION, BAGGAGE, SERVICE, OVERBOOKING, OTHER",
                    },
                    "description": {"type": "string", "description": "Detailed description of the complaint"},
                },
                "required": ["booking_ref", "passenger_name", "category", "description"],
            },
        },
    },
    {
        "type": "webhook",
        "name": "check_compensation",
        "description": (
            "Check if a passenger is eligible for EU Regulation 261/2004 compensation "
            "based on their booking reference. Returns eligibility status, reason, "
            "compensation amount in EUR (if applicable), route distance in km, "
            "and alternative flight options for cancellations. "
            "No authentication required."
        ),
        "api_schema": {
            "url": "https://skyitalia.yellowtest.it/compensation/check",
            "method": "GET",
            "query_params_schema": {
                "properties": {
                    "booking_ref": {"type": "string", "description": "Passenger booking reference e.g. XKRTMN"},
                },
                "required": ["booking_ref"],
            },
        },
    },
]


def update_agent_tools(tools):
    print(f"\n--- Updating agent {AGENT_ID} with {len(tools)} public tools ---")

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
        print("  [OK] Agent updated with public tools!")
        for t in tools:
            print(f"       + {t['name']}")
        return True
    else:
        print(f"  [FAIL] {resp.status_code} — {resp.text[:600]}")
        return False


if __name__ == "__main__":
    success = update_agent_tools(PUBLIC_TOOLS)

    if success:
        print("\n=== Phase 2 Complete ===")
        print(f"Agent: https://elevenlabs.io/app/conversational-ai/agents/{AGENT_ID}")
        print("\nTest with:")
        print("  - 'What is the status of flight AZ1235?'")
        print("  - 'What flights go from Milan to Paris?'")
        print("  - 'Look up my SkyMiles account, member ID LY002'")
        print("  - 'I want to file a complaint about my cancelled flight PLQWZF'")
        print("  - 'Am I eligible for compensation? My booking is PLQWZF'")
    else:
        print("\nPhase 2 failed. Check errors above.")
