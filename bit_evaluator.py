import os
import math
import shutil
import base64
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
# from dotenv import load_dotenv

# LangChain & Pydantic Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

# load_dotenv()
import os
import streamlit as st

# Mirror the secret value explicitly into the exact variable LangChain searches for
if "GEMINI_API_KEY" in os.environ:
    pass
elif "GEMINI_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

class BitPaperResult(BaseModel):
    reg_no: str = Field(description="The student registration number")
    faculty_total: float = Field(description="The total marks written by the faculty on the paper")
    answers: List[Optional[str]] = Field(description="List of 20 answers (A, B, C, or D). Use null for blanks or X marks.")

def clean_faculty_key(raw_input: str) -> List[str]:
    """
    Cleans the faculty input string into a list of 20 letters.
    Handles spaces, commas, and case sensitivity.
    """
    cleaned = re.findall(r'[A-D]', raw_input.upper())
    if len(cleaned) != 20:
        raise ValueError(f"Invalid Key: Expected 20 answers, but found {len(cleaned)}.")
    return cleaned

def encode_image(image_path):
    """Encodes image to base64 and ensures the file is released for movement."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def evaluate_student_bits(student_images, master_key: List[str]):
    """Core Evaluation Engine with Dynamic Key and Faculty Validation."""
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    parser = JsonOutputParser(pydantic_object=BitPaperResult)

    content = [
        {
            "type": "text",
            "text": (
                "Analyze these bit paper images.\n"
                "1. Extract 'reg_no'.\n"
                "2. Extract 'faculty_total' (marks written by teacher out of 10).\n"
                "3. Extract 20 answers.\n"
                f"{parser.get_format_instructions()}"
            )
        }
    ]

    for img_path in student_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_path)}"}
        })

    try:
        message = HumanMessage(content=content)
        response = llm.invoke([message])
        data = parser.parse(response.content)
        
        # 1. Calculation Logic vs Dynamic Key
        ans_list = data.get("answers", [])
        bit_marks = []
        correct_count = 0
        for i in range(len(master_key)):
            val = str(ans_list[i]).upper() if i < len(ans_list) and ans_list[i] else None
            if val == master_key[i]:
                bit_marks.append(0.5)
                correct_count += 1
            else:
                bit_marks.append(0.0)
        
        raw_sum = correct_count * 0.5
        ai_calculated_total = math.ceil(raw_sum)
        faculty_total = data.get("faculty_total", 0.0)

        # 2. Validation Logic: AI vs Faculty
        if ai_calculated_total != int(faculty_total):
            return {
                "status": "Error",
                "reg_no": data.get("reg_no", "UNKNOWN"),
                "message": f"Marks Mismatch: AI calculated {ai_calculated_total}, but Faculty wrote {faculty_total}."
            }
        
        return {
            "reg_no": data.get("reg_no"),
            "faculty_total": faculty_total,
            "bit_marks": bit_marks,
            "raw_sum": raw_sum,
            "final_score": ai_calculated_total,
            "status": "Success"
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}

def run_evaluation(raw_key_string: str):
    """
    Main entry point for evaluation.
    Accepts the raw key string from the UI (WhatsApp).
    """
    # 0. Clean the Master Key
    try:
        master_key = clean_faculty_key(raw_key_string)
    except ValueError as e:
        print(f"VERBOSE: {e}")
        return False

    base_path = Path("data/bit")
    process_dir = base_path / "process"
    success_dir = base_path / "success"
    error_dir = base_path / "error"
    reports_dir = base_path / "reports"
    
    for d in [success_dir, error_dir, reports_dir]: 
        d.mkdir(parents=True, exist_ok=True)

    all_jpgs = sorted(list(process_dir.glob("*.jpg")))
    if not all_jpgs:
        return False

    student_groups = {}
    for f in all_jpgs:
        parts = f.stem.split("_S")
        if len(parts) < 2: continue
        group_key = f"{parts[0]}_S{parts[1].split('_P')[0]}"
        student_groups.setdefault(group_key, []).append(f)

    file_results = {}
    error_logs = []
    current_pdf_stem = ""

    # --- Processing Loop ---
    for group_key, image_paths in student_groups.items():
        current_pdf_stem = group_key.split("_S")[0]
        print(f"VERBOSE: Validating {group_key} against Faculty Key...")
        
        eval_data = evaluate_student_bits(image_paths, master_key)
        
        if eval_data["status"] == "Success":
            print(f"  - [MATCH] {eval_data['reg_no']} -> {eval_data['final_score']}")
            row = {
                "File_Name": f"{current_pdf_stem}.pdf",
                "Regd_No": eval_data["reg_no"],
                "Faculty_Total": eval_data["faculty_total"],
                "AI_Total": eval_data["final_score"]
            }
            for idx, mark in enumerate(eval_data["bit_marks"]): row[f"Q{idx+1}"] = mark
            row["Raw_Sum"] = eval_data["raw_sum"]
            
            file_results.setdefault(current_pdf_stem, []).append(row)
            for img in image_paths: shutil.move(str(img), str(success_dir / img.name))
        else:
            print(f"  - [REJECTED] {group_key}: {eval_data['message']}")
            error_logs.append({
                "Source_PDF": f"{current_pdf_stem}.pdf",
                "Regd_No": eval_data.get("reg_no", "UNKNOWN"),
                "Student_Group": group_key,
                "Error_Detail": eval_data["message"],
                "Detected_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            for img in image_paths: shutil.move(str(img), str(error_dir / img.name))

    # --- Save Reports ---
    for pdf_stem, rows in file_results.items():
        csv_path = reports_dir / f"{pdf_stem}.csv"
        if csv_path.exists(): os.remove(csv_path)
        pd.DataFrame(rows).to_csv(csv_path, index=False)

    if error_logs:
        err_csv_path = reports_dir / f"{current_pdf_stem}_error_report.csv"
        if err_csv_path.exists(): os.remove(err_csv_path)
        pd.DataFrame(error_logs).to_csv(err_csv_path, index=False)

    return True

if __name__ == "__main__":
    # Test with a dummy key string (20 letters)
    test_key = "BDB CB BAB AB BCC DBBA AC" 
    run_evaluation(test_key)