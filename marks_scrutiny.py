import os
import base64
import shutil
from pathlib import Path
# from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# load_dotenv()
import os
import streamlit as st

# Mirror the secret value explicitly into the exact variable LangChain searches for
if "GEMINI_API_KEY" in os.environ:
    pass
elif "GEMINI_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- Pydantic Schema ---
class StudentMarks(BaseModel):
    reg_no: str = Field(description="The student registration number")
    descriptive: float = Field(description="Marks in descriptive section (max 15)")
    bit_paper: float = Field(description="Marks in bit paper section (max 10)")
    activity: float = Field(description="Marks in activity/assignment (max 5)")
    posted_total: float = Field(description="The total marks written by the faculty")

class AwardSheetData(BaseModel):
    students: List[StudentMarks]

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def run_scrutiny():
    """
    Main Scrutiny Engine:
    1. Reads image from /process
    2. Uses Gemini to extract and calculate
    3. Moves file to /success or /error
    4. Returns alerts for WhatsApp
    """
    base_path = Path("data/award_sheet")
    process_dir = base_path / "process"
    success_dir = base_path / "success"
    error_dir = base_path / "error"

    # Create directories if they don't exist
    for d in [success_dir, error_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Find the first image in process folder
    image_paths = list(process_dir.glob("*.jp*g"))
    if not image_paths:
        return "VERBOSE: No award sheet images found."

    target_img = image_paths[0]
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    parser = JsonOutputParser(pydantic_object=AwardSheetData)

    try:
        b64_image = encode_image(target_img)
        prompt = (
            "Analyze this Award Sheet image. Extract the data for all students in the table. "
            "Capture: reg_no, descriptive (15M), bit_paper (10M), activity (5M), and the posted_total. "
            f"{parser.get_format_instructions()}"
        )

        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
        ])

        response = llm.invoke([message])
        data = parser.parse(response.content)
        
        mismatch_data = []  # <--- Change this from a plain text list to a structured data list
        for student in data['students']:
            calc_total = student['descriptive'] + student['bit_paper'] + student['activity']
            if calc_total != student['posted_total']:
                mismatch_data.append({
                    "Student Reg No": student['reg_no'],
                    "Descriptive (15M)": student['descriptive'],
                    "Bit Paper (10M)": student['bit_paper'],
                    "Activity (5M)": student['activity'],
                    "Calculated Sum": calc_total,
                    "Faculty Posted Total": student['posted_total'],
                    "Discrepancy Margin": abs(calc_total - student['posted_total'])
                })

        # Move file to success tracking zone
        shutil.move(str(target_img), str(success_dir / target_img.name))
        
        # Return the structured data array directly to the UI
        return mismatch_data  

    except Exception as e:
        # Move to ERROR if AI fails to read the file entirely
        print(f"VERBOSE: Scrutiny Error - {e}")
        shutil.move(str(target_img), str(error_dir / target_img.name))
        return f"🚨 System Error: Could not process the award sheet. File moved to error folder."

if __name__ == "__main__":
    result = run_scrutiny()
    print(result)