import os
import sys
import json
import re
from datetime import datetime, timezone

# Load optional .env for local keys (python-dotenv optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Import optional dependencies
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from dateutil import parser as date_parser
except Exception:
    # minimal fallback for date parsing
    date_parser = None

# Read API key from environment if present
api_key = os.environ.get("OPENAI_API_KEY")

# OpenAI client placeholder
client = None

def _init_client_from_key(key: str):
    global client
    if OpenAI is None:
        return False
    try:
        client = OpenAI(api_key=key)
        return True
    except Exception:
        client = None
        return False

def set_api_key(key: str, persist_env: bool = False, write_dotenv: bool = False) -> bool:
    """Set the API key at runtime and (optionally) persist it.

    - key: API key string
    - persist_env: if True, set os.environ['OPENAI_API_KEY'] for current user session
    - write_dotenv: if True, write a local .env file with OPENAI_API_KEY (will be gitignored)

    Returns True if the client was successfully initialized.
    """
    global api_key, client
    if not key:
        return False
    api_key = key
    if persist_env:
        os.environ['OPENAI_API_KEY'] = key
    if write_dotenv:
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f'OPENAI_API_KEY={key}\n')
        except Exception:
            pass
    return _init_client_from_key(key)

<<<<<<< HEAD
def is_configured() -> bool:
    return client is not None
=======
ensure_dependencies()

# --- IMPORT AFTER INSTALLATION ---
import openai
from dateutil import parser as date_parser

# --- DETECT OPENAI SDK VERSION ---
try:
    from openai import OpenAI
    NEW_SDK = True
except ImportError:
    NEW_SDK = False

# --- PROMPT FOR API KEY ---
api_key = input("Please enter your OpenAI API key: ").strip()
if not api_key:
    raise ValueError("⚠️ You must provide a valid API key to continue.")

if NEW_SDK:
    client = OpenAI(api_key=api_key)
else:
    openai.api_key = api_key
>>>>>>> 2868a3086651f8c11d46f1a13a5370213f47fa49

# --- CRISIS MESSAGE ---
CRISIS_RESPONSE = (
    "I'm really sorry that you're feeling like this. You're not alone, and help is available right now.\n"
    "If you’re in Canada or the U.S., you can call or text **988** to reach the Suicide and Crisis Lifeline.\n"
    "If you're outside those areas, please reach out to your local emergency number or someone you trust."
)

# --- MEMORY STORAGE ---
memory = {
    "user_name": None,
    "pronouns": None,
    "age": None,
    "location": None,
    "parents": {},
    "siblings": {},
    "friends": {},
    "pets": {},
    "significant_others": {},
    "losses": [],
    "major_events": [],
    "recent_emotions": [],
    "coping_strategies": [],
    "conversation_history": [],
    "preferences": {"tone": None, "topics_to_avoid": [], "favorites": []},
    "crisis_info": {},
    "disasters": []
}

# --- HELPERS ---
def extract_time_from_text(text: str):
    try:
        dt = date_parser.parse(text, fuzzy=True)
        return dt.isoformat()
    except Exception:
        return None

def update_disasters(user_input: str):
    disasters_keywords = {
        "earthquake": "Drop, cover, and hold on. Stay away from windows and heavy objects.",
        "fire": "Stay low to avoid smoke, exit immediately if safe, and call emergency services.",
        "tornado": "Go to a safe room or basement. Avoid windows and stay sheltered.",
        "flood": "Move to higher ground immediately and avoid walking or driving in floodwaters.",
        "hurricane": "Follow evacuation orders and stay indoors away from windows.",
        "storm": "Stay indoors and away from tall objects, trees, and metal structures.",
        "tsunami": "Move to higher ground and follow evacuation routes."
    }
    text = user_input.lower()
    for disaster, advice in disasters_keywords.items():
        if disaster in text and not any(d.get("type") == disaster for d in memory["disasters"]):
            memory["disasters"].append({
                "type": disaster,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "advice": advice
            })

def update_losses_with_time(user_input: str):
    loss_pattern = r"(my|our)\s+(dad|mom|father|mother|brother|sister|friend|pet)\s*(\w*)\s*(died|passed|lost|killed|gone)"
    cause_pattern = r"(?:due to|in a|from a|because of|in a)\s+([\w\s]+)"
    matches = re.findall(loss_pattern, user_input.lower())
    cause_match = re.search(cause_pattern, user_input.lower())
    cause = cause_match.group(1) if cause_match else "unknown cause"
    for match in matches:
        person_type = match[1]
        person_name = match[2].capitalize() if match[2] else person_type.capitalize()
        timestamp = extract_time_from_text(user_input) or datetime.now(timezone.utc).isoformat()
        exists = any(l.get("person") == person_name and l.get("timestamp") == timestamp for l in memory["losses"])
        if not exists:
            memory["losses"].append({
                "person": person_name,
                "cause": cause,
                "timestamp": timestamp
            })

def check_for_time_question(user_input: str):
    text = user_input.lower()
    if "what time" in text or "when" in text:
        person_match = re.search(r"(my|our)?\s*(mom|dad|father|mother|brother|sister|friend|pet|\w+)", text)
        person_query = person_match.group(2).capitalize() if person_match else None
        if memory["losses"]:
            if person_query:
                for loss in reversed(memory["losses"]):
                    if loss["person"].lower() == person_query.lower():
                        person = loss["person"]
                        timestamp = loss["timestamp"]
                        cause = loss.get("cause", "unknown cause")
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            timestamp_str = dt.strftime("%I:%M %p on %A, %B %d, %Y")
                        except Exception:
                            timestamp_str = timestamp
                        return f"Your loved one {person} died at {timestamp_str} due to {cause}."
                return f"I don’t have a recorded time for {person_query}."
            else:
                latest_loss = memory["losses"][-1]
                person = latest_loss.get("person", "they")
                timestamp = latest_loss.get("timestamp", "an unknown time")
                cause = latest_loss.get("cause", "unknown cause")
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp_str = dt.strftime("%I:%M %p on %A, %B %d, %Y")
                except Exception:
                    timestamp_str = timestamp
                return f"Your loved one {person} died at {timestamp_str} due to {cause}."
        if memory["disasters"]:
            latest_disaster = memory["disasters"][-1]
            disaster = latest_disaster.get("type", "the disaster")
            timestamp = latest_disaster.get("timestamp", "an unknown time")
            advice = latest_disaster.get("advice", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp_str = dt.strftime("%I:%M %p on %A, %B %d, %Y")
            except Exception:
                timestamp_str = timestamp
            return f"The {disaster} happened at {timestamp_str}. Advice: {advice}"
        return "I’m not sure when that happened, but I can try to remember if you tell me."
    return None

# --- VERSION-AGNOSTIC OPENAI CALL ---
def get_chat_completion(system_prompt: str, user_input: str):
    if NEW_SDK:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    else:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()

# --- UPDATE MEMORY USING GPT ---
def update_memory_with_gpt(user_input: str) -> str:
    update_disasters(user_input)
    update_losses_with_time(user_input)

    # Crisis check
    crisis_keywords = ["kill myself", "suicide", "end my life", "want to die", "hurt myself"]
    if any(k in user_input.lower() for k in crisis_keywords):
        return CRISIS_RESPONSE

    memory_json = json.dumps(memory, ensure_ascii=False)
    system_prompt = (
        "You are a compassionate emotional support companion. You help users process grief, trauma, and emotions. "
        "You are not a therapist. If the user mentions self-harm, always return the CRISIS_RESPONSE message.\n\n"
        f"Current memory (JSON format): {memory_json}\n"
        "Instructions for GPT:\n"
        "1. Update the memory based on the user's input.\n"
        "2. If the user asks about a loved one's name or details, look it up in memory.\n"
        "3. Generate a compassionate, empathetic reply.\n"
        "4. Suggest coping strategies if appropriate.\n"
        "5. Always return valid JSON using double quotes only.\n"
        "6. The JSON format must be: {\"memory\": <updated_memory_json>, \"response\": \"<reply_text>\"}\n"
        "Do NOT return anything outside this JSON structure."
    )

    try:
        gpt_text = get_chat_completion(system_prompt, user_input)
        # Parse JSON safely
        start = gpt_text.find('{')
        end = gpt_text.rfind('}') + 1
        if start == -1 or end == -1:
            print("⚠️ GPT did not return valid JSON:\n", gpt_text)
            return "I'm here to listen. Can you tell me more about what's going on?"
        parsed = json.loads(gpt_text[start:end])
        updated_memory = parsed.get("memory", memory)
        reply_text = parsed.get("response", "I'm here to listen. Can you tell me more?")
        memory.update(updated_memory)
        return reply_text
    except Exception as e:
        # Provide a more actionable error message for debugging while keeping a gentle fallback for users.
        err_type = type(e).__name__
        print(f"⚠️ Mental health AI error ({err_type}): {e}")
        print("Hint: verify the 'openai' package is installed and that OPENAI_API_KEY is correctly set.")
        return "I'm here to listen. Can you tell me more about what's going on?"

# --- MAIN LOOP ---
def main():
    print("💬 Natural Disaster Companion")
    print("Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Bot: Take care of yourself. You’re not alone.")
            break
        time_response = check_for_time_question(user_input)
        if time_response:
            print(f"Bot: {time_response}\n")
            continue
        response = update_memory_with_gpt(user_input)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()
