from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# SQLite configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')


# Database model
class RoomBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    check_in = db.Column(db.String(20))
    check_out = db.Column(db.String(20))

# create Table
with app.app_context():
    db.create_all()

class HotelAgent:
    def __init__(self, db):
        self.db = db

    def handle(self, user_input, language="English"):
        user_input_lower = user_input.lower()

        if "check-in" in user_input_lower:
            return "Our check-in time is 3:00 PM."

        elif "restaurant" in user_input_lower or "dinner" in user_input_lower or "breakfast" in user_input_lower:
            return (
                "**Restaurant Hours**\n"
                "1. **Breakfast**\n"
                "🕒 7:00 AM – 10:00 AM\n"
                "📍 Ground Floor, Main Dining Area\n\n"
                "2. **Lunch**\n"
                "🕒 12:00 PM – 3:00 PM\n"
                "📍 Poolside Restaurant\n\n"
                "3. **Dinner**\n"
                "🕒 6:30 PM – 10:00 PM\n"
                "📍 Rooftop Sky Lounge\n\n"
                "4. **Room Service**\n"
                "🕒 Available 24/7\n"
                "📱 Dial ‘9’ from your room phone"
            )

        elif "my booking" in user_input_lower:
            # Example: hardcoded guest name (replace with actual auth/session)
            guest_name = "John Doe"
            booking = RoomBooking.query.filter_by(guest_name=guest_name).first()
            if booking:
                return f"{guest_name}, you have booked Room {booking.room_number} from {booking.check_in} to {booking.check_out}."
            else:
                return "Sorry, I couldn't find any booking for that name."

        # Fallback to Gemini
        return self.ask_gemini(user_input, language)

    def ask_gemini(self, user_input, language="English"):
        prompt = f"""
You are a hotel assistant. Respond in {language}. Answer in a helpful, friendly tone.
Guest: {user_input}
Assistant:
"""
        response = model.generate_content(prompt)
        return response.text.strip()

agent = HotelAgent(db)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        language = data.get("language", "English")

        if not user_input.strip():
            return jsonify({"error": "Empty message"}), 400

        reply = agent.handle(user_input, language)
        return jsonify({"response": reply})

    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Chat error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
