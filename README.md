# 🌍 AI Travel Planner Pro

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]()

## 📌 Overview
An AI agent that creates personalized travel itineraries through conversational interaction, combining:
- Google Gemini for natural language understanding
- Tavily API for real-time web search
- Streamlit for interactive UI

## 🛠️ Technical Implementation

### 🔑 Core Dependencies
python
# requirements.txt
streamlit==1.44.0
google-generativeai==0.8.4
tavily-python==0.0.5
python-dateutil==2.9.0
streamlit-extras==0.3.0
python-dotenv==1.0.1
#Ai Prompts
prompts = {
    "destination": "Extract ONLY the travel destination. Return JUST location name:",
    "dates": "Extract dates as 'MM/DD-MM/DD' or 'X days':",
    "budget": "Classify budget as 'low/medium/high':",
    "accommodation": "Identify accommodation type (hotel/hostel/etc.):"
}
#Dynamic Search Query Builder
# Builds Tavily search queries
f"{preferences} in {destination} with {budget} budget {'hidden gems' if hidden_gems else ''}"
# Itinerary Generation Prompt
"""
Generate {days}-day itinerary for {destination} with:
- Budget: {budget}
- Preferences: {preferences}
- Attractions: {attractions}
- Transport: {transport_modes[budget]}

Daily Structure:
## Day X: [Theme]
### Morning [Activity @ Location]
### Afternoon [Activity with Transport Notes]
### Evening [Dinner + Nightlife]
Include cost estimates and accessibility notes.
"""
"
#🔄 Conversation Flow Logic
# Simplified state machine
1. Get Destination → 2. Get Dates → 3. Get Budget → 
4. Get Duration → 5. Get Activities → 6. Get Food Preferences → 
7. Get Accommodation → 8. Find Attractions → 9. Generate Itinerary
#🚀 Deployment
#1.Local Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
#2.Cloud Deployment
Add requirements.txt with above dependencies

Include .env with:

Copy
GEMINI_API_KEY=your_key
TAVILY_API_KEY=your_key
💡 Key Features
Feature	Implementation	Example Input
Natural Date Parsing	dateutil.parser + custom logic	"next summer", "2 weeks in May"
Budget Tiers	Auto-classification	"medium budget", "not too expensive"
Preference Matching	Tavily filtered search	"museums and vegan food"
Error Recovery	Fallback search queries	Retries with broader parameters
📜 Sample Output
Generated Itinerary Excerpt

Copy
## Day 1: Historic Paris
### Morning
- 9:00 AM: Louvre Museum (€17, wheelchair accessible)
- Walk 15min to Café de Flore
- 12:00 PM: Lunch @ Café de Flore (vegan options)

### Afternoon
- 2:00 PM: Seine River Cruise (€15, departs Pont Neuf)
- Metro Line 4 to Montmartre
- 5:00 PM: Sacré-Cœur Basilica (free entry)
📋 Evaluation Criteria
✅ Prompt Design

Clear instructions with examples

Structured output formatting

✅ Prompt Chaining

Progressive refinement through 9 conversation steps

Context-aware follow-up questions

✅ Personalization

6 preference dimensions incorporated

Budget-aware recommendations

✅ Error Handling

Fallback search queries

Input validation at each step

📂 File Structure
travel-planner/
├── app.py                # Main application
├── requirements.txt      # Dependencies
├── .env                  # API keys
└── README.md             # Documentation
#📜 Sample Output
## Paris 5-Day Itinerary
**Budget**: Medium ($100/day)

### Day 1: Iconic Landmarks
- 9:00: Eiffel Tower (€25)
- 12:00: Lunch @ Le Jules Verne (vegan options)
- 15:00: Seine River Cruise (€15)
#📝 Requirements
streamlit==1.44.0
google-generativeai==0.8.4
tavily-python==0.0.5
python-dateutil==2.9.0
