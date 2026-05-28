import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pathlib import Path

# Import your existing pipelines
# (Make sure these filenames match exactly)
from pipeline import run_full_pipeline
from bit_pipeline import bit_orchestrator
from marks_scrutiny import run_scrutiny

app = Flask(__name__)

# This dictionary tracks the "State" for every phone number
# Example: {"+91987...": "AWAITING_CHOICE"}
user_sessions = {}

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    user_id = request.values.get('From')  # Get user's phone number
    incoming_msg = request.values.get('Body', '').strip().lower()
    
    resp = MessagingResponse()
    msg = resp.message()

    # --- 1. HANDLE NEW USERS / RESET ---
    if incoming_msg in ['hi', 'hello', 'menu', 'reset']:
        user_sessions[user_id] = "MENU"
        msg.body(
            "🎓 *AI Exam Auditor Menu*\n\n"
            "1️⃣ Descriptive Papers (Theory PDF)\n"
            "2️⃣ Bit Paper Scrutiny (MCQ PDF)\n"
            "3️⃣ Total Marks Scrutiny (Award Sheet JPG)\n\n"
            "Reply with *1, 2, or 3* to proceed."
        )
        return str(resp)

    # --- 2. HANDLE MENU SELECTION ---
    current_state = user_sessions.get(user_id)

    if current_state == "MENU":
        if incoming_msg == '1':
            user_sessions[user_id] = "WAITING_THEORY_PDF"
            msg.body("📂 *Mode: Theory Grading*\nPlease upload your PDF file.")
        elif incoming_msg == '2':
            user_sessions[user_id] = "WAITING_BIT_PDF"
            msg.body("📂 *Mode: Bit Paper*\nPlease upload your PDF file.")
        elif incoming_msg == '3':
            user_sessions[user_id] = "WAITING_AWARD_SHEET"
            msg.body("📂 *Mode: Total Scrutiny*\nPlease upload the Award Sheet image.")
        else:
            msg.body("❌ Invalid choice. Please reply with 1, 2, or 3.")
        return str(resp)

    # --- 3. HANDLE FILE UPLOADS ---
    # Check if the user sent a file (Media)
    num_media = int(request.values.get('NumMedia', 0))
    
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')
        content_type = request.values.get('MediaContentType0')
        
        # User-specific folder setup
        user_folder_name = user_id.replace(":", "_").replace("+", "")
        
        if current_state == "WAITING_THEORY_PDF" and 'pdf' in content_type:
            save_path = f"data/pdf_files/{user_folder_name}_theory.pdf"
            download_file(media_url, save_path)
            msg.body("⚙️ Processing Theory Paper... Please wait for the CSV report.")
            # run_full_pipeline() # Trigger your logic here
            user_sessions[user_id] = "MENU"

        elif current_state == "WAITING_BIT_PDF" and 'pdf' in content_type:
            save_path = f"data/bit/pdf_files/{user_folder_name}_bit.pdf"
            download_file(media_url, save_path)
            msg.body("⚙️ Bit Paper received. (Next step: Ask for Key/Pages tomorrow!)")
            user_sessions[user_id] = "MENU"

        elif current_state == "WAITING_AWARD_SHEET" and 'image' in content_type:
            save_path = f"data/award_sheet/process/{user_folder_name}_sheet.jpg"
            download_file(media_url, save_path)
            msg.body("⚙️ Scrutinizing Award Sheet...")
            result = run_scrutiny() # This will move files to success/error
            msg.body(f"📊 *Scrutiny Result:*\n{result}")
            user_sessions[user_id] = "MENU"
        else:
            msg.body("❌ Please upload the correct file type for your selection.")
    else:
        msg.body("⚠️ No file detected. Please upload a file or type 'hi' for menu.")

    return str(resp)

def download_file(url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    r = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(r.content)

if __name__ == "__main__":
    app.run(port=5000)