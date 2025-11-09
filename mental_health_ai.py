import json
import os
import re
from datetime import datetime, timezone
from dateutil import parser as date_parser  # pip install python-dateutil
from openai import OpenAI

# Hardcoded OpenAI API key (replace with your actual key)
api_key = "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"

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Crisis message
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
    "losses": [],  # {"person": str, "cause": str, "timestamp": str}
    "major_events": [],
    "recent_emotions": [],
    "coping_strategies": [],
    "conversation_history": [],
    "preferences": {"tone": None, "topics_to_avoid": [], "favorites": []},
    "crisis_info": {},
    "disasters": []  # {"type": str, "timestamp": str, "advice": str}
}

# --- HELPERS ---
def extract_time_from_text(text: str):
    """Parse datetime from user text; return ISO string if found."""
    try:
        dt = date_parser.parse(text, fuzzy=True)
        return dt.isoformat()
    except Exception:
        return None

def update_disasters(user_input: str):
    """Detect natural disasters and add them to memory with timestamp and advice."""
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
    """Detect mentions of loved ones dying; store with timestamp, name, and cause."""
    # Matches explicit statements that a person died
    loss_pattern = r"(my|our)\s+(dad|mom|father|mother|brother|sister|friend|pet)\s*(\w*)\s*(died|passed|lost|killed|gone)"
    cause_pattern = r"(?:due to|in a|from a|because of|in a)\s+([\w\s]+)"

    matches = re.findall(loss_pattern, user_input.lower())
    cause_match = re.search(cause_pattern, user_input.lower())
    cause = cause_match.group(1) if cause_match else "unknown cause"

    for match in matches:
        person_type = match[1]
        person_name = match[2].capitalize() if match[2] else person_type.capitalize()

        # Extract time from text
        timestamp = extract_time_from_text(user_input) or datetime.now(timezone.utc).isoformat()

        # Avoid duplicates for same person + timestamp
        exists = any(l.get("person") == person_name and l.get("timestamp") == timestamp for l in memory["losses"])
        if not exists:
            memory["losses"].append({
                "person": person_name,
                "cause": cause,
                "timestamp": timestamp
            })

def check_for_time_question(user_input: str):
    """If the user asks about when something happened, retrieve the timestamp from memory."""
    text = user_input.lower()
    if "what time" in text or "when" in text:
        # Extract a person name or type if mentioned
        person_match = re.search(r"(my|our)?\s*(mom|dad|father|mother|brother|sister|friend|pet|\w+)", text)
        person_query = person_match.group(2).capitalize() if person_match else None

        # Check losses
        if memory["losses"]:
            if person_query:
                # Try to find that person
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
                # No specific person, return the most recent
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

        # Check disasters
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

def update_memory_with_gpt(user_input: str) -> str:
    """Send user input and current memory to GPT to update memory and generate a compassionate reply."""
    update_disasters(user_input)
    update_losses_with_time(user_input)

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=400,
            temperature=0.7
        )

        gpt_text = response.choices[0].message.content.strip()
        parsed = json.loads(gpt_text)
        updated_memory = parsed.get("memory", memory)
        reply_text = parsed.get("response", "I'm here to listen. Can you tell me more?")
        memory.update(updated_memory)

        return reply_text

    except json.JSONDecodeError:
        return "I'm here to listen. Can you tell me more about what's going on?"
    except Exception:
        return "I'm here to listen. Can you tell me more about what's going on?"

# --- MAIN LOOP ---
def main():
    print("💬 Natural Disastor Companion")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Bot: Take care of yourself. You’re not alone.")
            break

        # First, check if the user is asking about a remembered time
        time_response = check_for_time_question(user_input)
        if time_response:
            print(f"Bot: {time_response}\n")
            continue

        # Otherwise, use GPT for general emotional conversation
        response = update_memory_with_gpt(user_input)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()


