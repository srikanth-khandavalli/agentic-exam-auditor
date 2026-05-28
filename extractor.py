import os
import base64
from typing import Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# load_dotenv()
import os
import streamlit as st

# Mirror the secret value explicitly into the exact variable LangChain searches for
if "GEMINI_API_KEY" in os.environ:
    pass
elif "GEMINI_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

class QuestionRow(BaseModel):
    a: int = Field(description="Marks for sub-question 'a'. Use 0 if blank.")
    b: int = Field(description="Marks for sub-question 'b'. Use 0 if blank.")
    c: int = Field(description="Marks for sub-question 'c'. Use 0 if blank.")
    d: int = Field(description="Marks for sub-question 'd'. Use 0 if blank.")
    row_total: int = Field(description="The total marks written at the end of this specific row.")

class ExamFrontPage(BaseModel):
    registration_number: str = Field(description="The student's registration number, e.g., 24B01A4576")
    q1: QuestionRow
    q2: QuestionRow
    q3: QuestionRow
    q4: QuestionRow
    q5: QuestionRow
    q6: QuestionRow
    total_marks_written: int = Field(description="The grand total marks written (usually out of 30)")
    scaled_marks: int = Field(description="The marks scaled to 15")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_marks_from_image(image_path: str):
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ExamFrontPage)
    
    # structured_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(ExamFrontPage)
    
    base64_image = encode_image(image_path)
    
    message = HumanMessage(
        content=[
            {
                "type": "text", 
                "text": (
                    "You are a meticulous data entry auditor. Extract marks from the exam front page table. "
                    "The table has exactly 6 rows (Questions 1 to 6). "
                    "Each row has 4 columns for sub-questions (a, b, c, d) and a 'Total' column. "
                    "Even if a cell is empty or has a dash, record it as 0. "
                    "Registration Number format: 2 digits, then a LETTER (look closely, e.g., 'B' not '8'), then rest."
                )
            },
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    )
    
    print(f"Sending {image_path} to Gemini...")
    # print(f"Sending {image_path} to OpenAI...")
    return structured_llm.invoke([message])