
import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from anthropic import Anthropic

# Load private API key
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


# WEBSITE PAGES

@app.route("/")
@app.route("/index.html")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/explore.html")
def explore():
    return send_from_directory(BASE_DIR, "explore.html")


@app.route("/itinerary.html")
def itinerary():
    return send_from_directory(BASE_DIR, "itinerary.html")


@app.route("/journal.html")
def journal():
    return send_from_directory(BASE_DIR, "journal.html")

@app.route("/article.html")
def article():
    return send_from_directory(BASE_DIR, "article.html")

@app.route("/articles/<filename>")
def individual_article(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "articles"),
        filename
    )
    
# SOLO ACTIVITY GENERATOR

@app.route("/api/idea", methods=["POST"])
def create_idea():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Please enter a city."}), 400

        city = data.get("city", "").strip()
        avoid = data.get("avoid", [])

        if not city:
            return jsonify({"error": "Please enter a city."}), 400

        avoidance = ""
        if avoid:
            avoidance = (
                " Do not repeat these already-given ideas: "
                + " | ".join(avoid[-4:])
            )

        prompt = (
            f"Give ONE short, fun, specific thing for a solo traveler "
            f"to do today in {city}. "
            "Maximum 12 words. Casual, upbeat, playful tone. "
            "Must name a real, specific place. "
            "You may add one fitting emoji. "
            "No quotes, no preamble, just the tip."
            + avoidance
            + ' Examples: "Hop the train to Howth and hike the cliffs 🌊" '
            '"Grab strawberries at Borough Market".'
        )

        message = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        idea = ""

        for block in message.content:
            if block.type == "text":
                idea += block.text

        idea = idea.strip().strip('"').strip("'")

        if not idea:
            return jsonify({"error": "Claude returned an empty idea."}), 500

        return jsonify({
            "success": True,
            "idea": idea
        })

    except Exception:
        app.logger.exception("Activity generation failed")
        return jsonify({
            "error": "We couldn't generate an idea. Please try again."
        }), 500


# AI ITINERARY GENERATOR

@app.route("/api/itinerary", methods=["POST"])
def create_itinerary():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Please enter your trip details."}), 400

        destination = data.get("destination", "").strip()
        days = data.get("days", "")
        budget = data.get("budget", "")
        travel_style = data.get("travelStyle", "")
        interests = data.get("interests", "")
        travel_type = data.get("travelType", "Solo")

        if not destination:
            return jsonify({"error": "Please enter a destination."}), 400

        prompt = f"""
        Create a personalized travel itinerary.

        Destination: {destination}
        Trip duration: {days}
        Daily budget: {budget}
        Travel style: {travel_style}
        Interests: {interests}
        Traveling with: {travel_type}

        Organize the itinerary by day.

        For each day include:
        - Morning activities
        - Lunch recommendations
        - Afternoon activities
        - Dinner recommendations
        - Evening activities

        Also include:
        - Local experiences
        - Popular and lesser-known attractions
        - Budget-friendly suggestions
        - Transportation tips
        - Solo travel safety tips when relevant

        Make the itinerary realistic and easy to follow.
        Use clear headings and readable formatting.
        Do not invent exact opening hours, prices, or availability.
        Remind the traveler to verify details before visiting.
        """

        message = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=2500,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        itinerary_text = ""

        for block in message.content:
            if block.type == "text":
                itinerary_text += block.text

        return jsonify({
            "success": True,
            "itinerary": itinerary_text
        })

    except Exception:
        app.logger.exception("Itinerary generation failed")
        return jsonify({
            "error": "We couldn't create your itinerary. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
