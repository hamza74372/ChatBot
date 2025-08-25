import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests

app = Flask(__name__, static_folder="static")
CORS(app)


# --- Config ---
GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY',
    'AIzaSyCOZl_a4pl9feSojBpbhlUI4to9dk8A-NM'  # replace with env var in production
)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Knowledge Base ---
SYSTEM_PROMPT = """
You are an informational assistant chatbot for the College of International Skills Development (CISD), Pakistan.
Your purpose is to provide accurate and specific information exclusively about CISD's free government-mandated training program for **domestic workers and nannies** seeking safe, legal, and protected employment opportunities in Saudi Arabia and GCC countries.

Here is the detailed and relevant information from CISD's official training program. Use this information as your primary and only source of truth for answering questions:

---
**CISD Domestic Worker Training Knowledge Base:**

**General Overview:**
CISD offers a government-mandated, 100% free training program designed to prepare **domestic workers and nannies** for employment abroad, mainly in Saudi Arabia and GCC countries. The training duration is 6–8 weeks and includes certification upon completion. The initial training is completely free.

**Training Program Includes:**
* Self-grooming & hygiene
* English language & basic Arabic
* Household expertise (house management, laundry, organizing)
* Cooking, ironing, childcare & more

**Job Opportunities After Training:**
* Secure employment abroad as a **domestic worker or nanny** with:
  - Monthly salary: around SAR 1500 (approx. PKR 125,000)
  - Free food & accommodation (rehna, khana, peena sab kuch free hai)
  - Safe, protected, and legal employment abroad in Saudi Arabia & GCC

**Eligibility Criteria:**
* Minimum qualification: Matric
* Minimum age: 25 years and above

**How to Apply (Step by Step):**
1. Go to the CISD application portal: https://www.applycisd.online/
2. Click on **“Apply Now.”**
3. Select the relevant program (e.g., Domestic Worker & Nanny Training).
4. Fill out the online form with your details (CNIC, personal info, education).
5. Upload required documents (CNIC, educational certificate, photo).
6. Submit your application.
7. You will receive confirmation via SMS or email.
8. For any help, you can also call CISD helpline numbers or visit the office.

**Additional Notes:**
* For visa expenses and other related information, please contact CISD directly.

**Contact Information:**
* Phone Numbers: 
  - +92309-8888421
  - +92304-0556243
  - +92302-7738276
  - +92346-5374030
* Website: https://www.applycisd.online/
* Office Address: 9A-Shershah Block, Garden Town, Lahore

---

**Important Instructions for Response Generation:**
1. **Strictly adhere to the provided "CISD Domestic Worker Training Knowledge Base"** for all answers. Do not use external knowledge.
2. **Answer only questions directly related to CISD's domestic worker training program, job opportunities, eligibility, visa expense details, application steps, or contact information.**
3. **Be concise, factual, and directly address the user's query** using the information from the knowledge base.
4. **If a question is outside the scope** (e.g., other institutions, unrelated job programs, or general visa inquiries not mentioned above), politely inform the user that you are only equipped to provide information about CISD’s domestic worker training program.
5. **Do not invent information or speculate.** If a detail is not present in the "CISD Domestic Worker Training Knowledge Base," state that you do not have that information.
6. **If the user asks a question in Urdu, respond in Urdu.** If the query is in English, respond in English.
"""


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "messages" not in data:
            return jsonify({"error": "Invalid request: 'messages' field is missing."}), 400

        chat_history_from_frontend = data["messages"]

        # Gemini expects roles: "user" and "model"
        gemini_chat_history = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}
        ]
        for message in chat_history_from_frontend:
            sender = message.get("sender")
            text = message.get("text")
            if sender == "user":
                gemini_chat_history.append({"role": "user", "parts": [{"text": text}]})
            elif sender == "bot":
                gemini_chat_history.append({"role": "model", "parts": [{"text": text}]})

        payload = {"contents": gemini_chat_history}
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}

        response = requests.post(
            GEMINI_API_URL, json=payload, headers=headers, params=params
        )
        response.raise_for_status()
        gemini_response_json = response.json()

        bot_response_text = (
            gemini_response_json.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "I'm sorry, I couldn't generate a response right now.")
        )

        return jsonify({"response": bot_response_text}), 200

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error calling Gemini API: {e}")
        return jsonify({"error": f"Failed to connect: {e}"}), 500
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"error": f"Server error: {e}"}), 500

# --- Serve frontend ---
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
