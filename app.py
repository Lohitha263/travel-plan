import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from tavily import TavilyClient
from streamlit_extras.let_it_rain import rain
import os
from dotenv import load_dotenv

# --- Environment Setup ---
load_dotenv()
load_dotenv()  # Load environment variables from .env file

# --- API Configuration with Error Handling ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    st.error(f"Failed to initialize APIs: {str(e)}")
    st.stop()

# --- Animations ---
def add_confetti():
    rain(emoji="🎉", animation_length=1)

def type_message(text):
    message = st.empty()
    display_text = ""
    for char in text:
        display_text += char
        message.markdown(f'<div style="font-family: sans-serif">{display_text}</div>', unsafe_allow_html=True)
        time.sleep(0.02)
    return message

# --- Improved Date Parsing ---
def parse_flexible_date(date_str):
    try:
        if "summer" in date_str.lower():
            year = datetime.now().year
            if "next" in date_str.lower():
                year += 1
            return f"06/15-08/31/{year}"
        elif "winter" in date_str.lower():
            year = datetime.now().year
            if "next" in date_str.lower():
                year += 1
            return f"12/01-02/28/{year}"
        elif "week" in date_str.lower():
            parts = date_str.split()
            if len(parts) >= 3:
                duration = int(parts[1])
                month = parts[3]
                start_date = parse(f"1 {month}").replace(day=1)
                end_date = start_date + relativedelta(days=duration*7)
                return f"{start_date.strftime('%m/%d')}-{end_date.strftime('%m/%d')}"
        elif "-" in date_str or "to" in date_str:
            return date_str.replace("to", "-")
        else:
            parsed = parse(date_str, fuzzy=True)
            return parsed.strftime("%m/%d/%Y")
    except Exception as e:
        print(f"Date parsing error: {e}")
        return None

# --- Core Functions with Enhanced Error Handling ---
def is_greeting(text):
    text = text.lower().strip()
    greetings = ["hi", "hello", "hey", "hii", "hola", "greetings"]
    return text in greetings

def is_affirmative(text):
    text = text.lower().strip()
    return any(word in text for word in ["yes", "yeah", "yep", "ok", "sure", "please", "yup"])

def is_negative(text):
    text = text.lower().strip()
    return any(word in text for word in ["no", "nope", "not", "never", "nah"])

def extract_info(text, info_type):
    prompts = {
        "destination": "Extract ONLY the travel destination from this text. Return JUST the location name or empty string if none found:",
        "dates": "Extract travel dates or duration from this text. Return as 'MM/DD-MM/DD' or 'X days' format:",
        "budget": "Extract budget information from this text. Return as 'low/medium/high' or empty string:",
        "preferences": "Extract travel preferences from this text focusing on activities, interests, and style:",
        "food_preferences": "Extract food preferences from this text (vegetarian/vegan/gluten-free/etc.):",
        "special_needs": "Extract special requirements from this text (wheelchair accessible/family-friendly/etc.):",
        "accommodation": "Extract accommodation preferences from this text (hotel/hostel/villa/airbnb/luxury/budget/etc.):"
    }
    try:
        response = model.generate_content(f"{prompts[info_type]} '{text}'")
        return response.text.strip()
    except Exception as e:
        st.error(f"Error extracting {info_type}: {str(e)}")
        return ""

def find_attractions(destination, preferences="", budget="", hidden_gems=False, food_type=""):
    try:
        with st.spinner(f"🔍 Finding the best {preferences} in {destination}..."):
            query_parts = [
                f"{preferences} activities in {destination}",
                f"{budget} budget" if budget else "",
                "off the beaten path less touristy" if hidden_gems else "",
                f"{food_type} friendly" if food_type and food_type != "no restrictions" else "",
                "for tourists official sites"
            ]
            query = " ".join(filter(None, query_parts))
            
            results = tavily.search(query=query, include_answer=True, max_results=5)
            
            if not results or 'results' not in results or len(results['results']) == 0:
                st.warning("Couldn't find attractions matching your criteria. Trying a broader search...")
                # Fallback search without preferences
                results = tavily.search(query=f"things to do in {destination}", include_answer=True, max_results=5)
                if not results or 'results' not in results:
                    return []
            
            return [{
                'name': r.get('title', 'Unknown'),
                'url': r.get('url', '#'),
                'snippet': (r.get('content', '')[:150] + '...') if r.get('content') else 'No description available'
            } for r in results.get('results', [])]
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def find_accommodations(destination, budget="", accommodation_type=""):
    try:
        with st.spinner(f"🏨 Finding {accommodation_type} accommodations in {destination}..."):
            query_parts = [
                f"{accommodation_type} accommodations in {destination}",
                f"{budget} budget" if budget else "",
                "official sites"
            ]
            query = " ".join(filter(None, query_parts))
            
            results = tavily.search(query=query, include_answer=True, max_results=3)
            
            if not results or 'results' not in results or len(results['results']) == 0:
                st.warning("Couldn't find accommodations matching your criteria. Trying a broader search...")
                results = tavily.search(query=f"hotels in {destination}", include_answer=True, max_results=3)
                if not results or 'results' not in results:
                    return []
            
            return [{
                'name': r.get('title', 'Unknown'),
                'url': r.get('url', '#'),
                'snippet': (r.get('content', '')[:150] + '...') if r.get('content') else 'No description available',
                'type': accommodation_type if accommodation_type else 'hotel'
            } for r in results.get('results', [])]
    except Exception as e:
        st.error(f"Accommodation search error: {str(e)}")
        return []

def generate_itinerary(destination, days, preferences, attractions, budget, start_date, food_type="", accommodations=[]):
    transport_modes = {
        "low": "public transport and walking",
        "medium": "taxis and occasional public transport",
        "high": "private transfers and premium transportation"
    }
    
    food_context = f"\n- Dietary preferences: {food_type}" if food_type and food_type != "no restrictions" else ""
    accommodation_context = ""
    
    if accommodations:
        accommodation_context = "\n- Recommended accommodations:\n"
        for acc in accommodations[:2]:  # Show top 2 options
            accommodation_context += f"  - [{acc['name']}]({acc['url']}) ({acc['type']})\n"
    
    prompt = f"""Create a detailed {days}-day itinerary for {destination} starting on {start_date} with:
    - Budget level: {budget}
    - Focus: {preferences}
    {food_context}
    {accommodation_context}
    - Transportation: {transport_modes.get(budget, "mix of transport options")}
    - Must include these attractions: {[a['name'] for a in attractions]}
    
    Format with this structure for each day:
    ## Day X: [Theme/Area]
    ### Morning
    - 9:00 AM: [Activity with specific venue name]
    - 12:00 PM: [Lunch suggestion matching {budget} budget and {food_type if food_type != 'no restrictions' else 'any'} dietary needs]
    
    ### Afternoon 
    - 2:00 PM: [Activity]
    - 5:00 PM: [Optional coffee/tea break]
    
    ### Evening
    - 7:00 PM: [Dinner suggestion]
    - 9:00 PM: [Optional night activity]
    
    Include:
    - Estimated costs for key activities
    - Transportation tips between locations (specific routes/modes)
    - Travel times between locations
    - Links to official websites when available
    - Specific notes about dietary options at each food venue
    - Recommended accommodations nearby if not already provided"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't generate the itinerary. Error: {str(e)}"

# --- Enhanced Conversation Handler ---
def handle_conversation():
    last_msg = st.session_state.messages[-1]["content"].strip().lower()
    
    # Initial greeting
    if len(st.session_state.messages) == 1:
        if is_greeting(last_msg):
            return "Hello! 😊 I'm your travel planning assistant. Where would you like to go?"
        return "Hi there! ✈️ Let's plan your trip. Where would you like to travel?"

    # Get destination
    if "destination" not in st.session_state:
        if not is_greeting(last_msg):
            extracted = extract_info(last_msg, "destination")
            if extracted:
                st.session_state.destination = extracted
                return f"Great choice! {extracted} sounds wonderful. When will you be visiting? (Example: 'next summer' or 'July 15-22')"
            st.session_state.destination = last_msg  # Fallback to raw input
            return f"I'll assume you want to visit {last_msg}. When will you be traveling?"
        return "I'd love to help plan your trip! Where would you like to go? (Example: 'Japan' or 'I want to visit Paris')"

    # Get dates
    if "dates" not in st.session_state:
        dates = extract_info(last_msg, "dates")
        if dates:
            parsed_date = parse_flexible_date(dates)
            if parsed_date:
                st.session_state.dates = parsed_date
                st.session_state.start_date = parsed_date.split('-')[0] if '-' in parsed_date else parsed_date
                return "What's your budget range? (low/medium/high)"
            else:
                return "I couldn't understand those dates. Please try again (Example: 'next summer' or 'August 10-17')"
        return "When will you be visiting? (Example: 'next month' or 'August 10-17')"

    # Get budget
    if "budget" not in st.session_state:
        budget = extract_info(last_msg, "budget")
        if budget.lower() in ["low", "medium", "high"]:
            st.session_state.budget = budget.lower()
            return f"Got your {budget} budget preference. How many days will you be in {st.session_state.destination}?"
        return "Please specify your budget as low, medium, or high (Example: 'medium budget')"

    # Get duration
    if "days" not in st.session_state:
        if last_msg.isdigit():
            st.session_state.days = last_msg
            return "What types of activities interest you? (Examples: 'museums', 'hiking', 'food tours')"
        return "Please enter the number of days (Example: '7' or '10 days')"

    # Get activities
    if "activities" not in st.session_state:
        if not last_msg:
            return "Please share what activities you'd enjoy (Example: 'I love museums and walking tours')"
        st.session_state.activities = last_msg
        return "Any dietary preferences? (Examples: 'vegetarian', 'local food', or 'no preferences')"

    # Get food preferences
    if "food_type" not in st.session_state:
        st.session_state.food_type = last_msg if last_msg != "no preferences" else "no restrictions"
        return "What type of accommodation do you prefer? (Examples: 'hotel', 'hostel', 'airbnb', 'luxury resort')"

    # Get accommodation preferences
    if "accommodation_type" not in st.session_state:
        st.session_state.accommodation_type = last_msg if last_msg != "no preference" else "any"
        return "Any special requirements? (Examples: 'wheelchair accessible', 'family-friendly', or 'none')"

    # Get special needs
    if "special_needs" not in st.session_state:
        st.session_state.special_needs = last_msg if last_msg != "none" else "none"
        st.session_state.preferences = (
            f"Activities: {st.session_state.activities}\n"
            f"Food: {st.session_state.food_type}\n"
            f"Accommodation: {st.session_state.accommodation_type}\n"
            f"Special needs: {st.session_state.special_needs}"
        )
        
        # Find accommodations first
        st.session_state.accommodations = find_accommodations(
            st.session_state.destination,
            st.session_state.budget,
            st.session_state.accommodation_type
        )
        
        return (
            f"Perfect! For your {st.session_state.days}-day trip to {st.session_state.destination} with a {st.session_state.budget} budget:\n"
            f"- Activities: {st.session_state.activities}\n"
            f"- Food: {st.session_state.food_type}\n"
            f"- Accommodation: {st.session_state.accommodation_type}\n"
            f"- Special needs: {st.session_state.special_needs}\n\n"
            "Should I focus on:\n"
            "1. Popular tourist spots\n"
            "2. Local hidden gems\n"
            "3. A mix of both\n\n"
            "Reply with 1, 2, or 3"
        )

    # Handle attraction style
    if "hidden_gems" not in st.session_state:
        if last_msg in ["1", "2", "3"]:
            st.session_state.hidden_gems = {
                "1": False,
                "2": True,
                "3": True
            }[last_msg]
            
            st.session_state.attractions = find_attractions(
                st.session_state.destination,
                st.session_state.activities,
                st.session_state.budget,
                st.session_state.hidden_gems,
                st.session_state.food_type
            )
            
            if not st.session_state.attractions:
                return "Couldn't find matching activities. Want to try different preferences?"
            
            reply = "Here's what I found:\n"
            for i, a in enumerate(st.session_state.attractions[:3], 1):
                reply += f"\n{i}. [{a['name']}]({a['url']}) - {a['snippet']}"
            
            if st.session_state.accommodations:
                reply += "\n\nRecommended accommodations:\n"
                for i, a in enumerate(st.session_state.accommodations[:2], 1):
                    reply += f"\n{i}. [{a['name']}]({a['url']}) - {a['snippet']}"
            
            reply += "\n\nReady to create your itinerary? (yes/no)"
            return reply
        return "Please choose 1, 2, or 3 for attraction style"

    # Generate itinerary
    if is_affirmative(last_msg) and not st.session_state.get("itinerary_generated"):
        itinerary = generate_itinerary(
            st.session_state.destination,
            st.session_state.days,
            st.session_state.preferences,
            st.session_state.attractions,
            st.session_state.budget,
            st.session_state.get("start_date", "your dates"),
            st.session_state.food_type,
            st.session_state.accommodations
        )
        add_confetti()
        st.session_state.itinerary_generated = True
        return (
            f"**Your {st.session_state.days}-Day {st.session_state.destination} Itinerary** ✈️\n\n"
            f"Budget: {st.session_state.budget}\n\n"
            f"{itinerary}\n\n"
            "What would you like to do next?\n"
            "1. Save this itinerary\n"
            "2. Make changes\n"
            "3. Start a new trip"
        )
    
    # Handle post-itinerary options
    if st.session_state.get("itinerary_generated"):
        if last_msg in ["1", "2", "3"]:
            if last_msg == "1":
                st.session_state.saved_itinerary = True
                return "Itinerary saved! Would you like to start a new trip? (yes/no)"
            elif last_msg == "2":
                # Reset specific parameters for changes
                keys_to_keep = ["destination", "dates", "start_date", "messages"]
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                return "What would you like to change? (budget, days, activities, etc.)"
            elif last_msg == "3":
                # Reset everything for a new trip
                st.session_state.clear()
                st.session_state.messages = [{"role": "assistant", "content": "Let's plan a new trip! Where would you like to go?"}]
                return None
        
        # Handle yes/no after saving
        if st.session_state.get("saved_itinerary"):
            if is_affirmative(last_msg):
                st.session_state.clear()
                st.session_state.messages = [{"role": "assistant", "content": "Great! Where would you like to go next?"}]
                return None
            elif is_negative(last_msg):
                del st.session_state.saved_itinerary
                return "You can:\n1. View your saved itineraries\n2. Exit the planner\n\nWhat would you like to do?"
    
    # Handle negative responses
    if is_negative(last_msg):
        if "itinerary_generated" in st.session_state:
            return "What would you like to change about your itinerary? You can update:\n- Destination\n- Dates\n- Budget\n- Activities\nOr say 'start over'"
        return "What would you like to do instead?"
    
    return "I didn't understand that. Please try again or say 'help' for options."

# --- Main App ---
def main():
    st.set_page_config(page_title="🌍 Travel Planner Pro", page_icon="✈️", layout="wide")
    st.title("✈️ Your Personal Travel Assistant")
    
    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your travel assistant. Where would you like to go?"}]
    
    # Display chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Handle input
    if prompt := st.chat_input("Type your message here..."):
        if prompt.lower() == "help":
            st.session_state.messages.append({"role": "user", "content": prompt})
            help_text = """**Help Menu**\n- To start over, say "start over"\n- To change something, say "change [thing]"\n- Need more help? Just describe what you're trying to do!"""
            st.session_state.messages.append({"role": "assistant", "content": help_text})
            return
        
        if prompt.lower() == "start over":
            st.session_state.clear()
            st.session_state.messages = [{"role": "assistant", "content": "Okay, let's start fresh! Where would you like to go?"}]
            return
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            thinking = st.empty()
            thinking.markdown("✈️ Planning...")
            
            response = handle_conversation()
            if response:
                message = type_message(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            thinking.empty()

if __name__ == "__main__":
    main()