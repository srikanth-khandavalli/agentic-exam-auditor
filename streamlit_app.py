import streamlit as st
import os
import pandas as pd
from pathlib import Path
from PIL import Image

# Import your core back-end engines
from pipeline import run_full_pipeline
from bit_pipeline import bit_orchestrator
from marks_scrutiny import run_scrutiny
# import google as genai
from google import genai
# 1. Check if the secret exists
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🚨 CRITICAL ERROR: `GEMINI_API_KEY` not found in Streamlit Secrets!")
    st.stop()

# 2. Initialize the modern Client using the secrets pointer
# This client object is what you'll pass or use to interact with gemini-2.5-flash
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Force the instantiation of your entire lineage data tree structure
def initialize_storage_architecture():
    directories = [
        "data/pdf_files",
        "data/reports",
        "data/bit/pdf_files",
        "data/bit/reports",
        "data/award_sheet/process"
    ]
    for folder in directories:
        Path(folder).mkdir(parents=True, exist_ok=True)

initialize_storage_architecture()

st.set_page_config(page_title="AI Exam Auditor", layout="wide", page_icon="🎓")

# --- APP HEADER ---
st.title("🎓 AI Exam Auditor & Grading Assistant")
st.markdown("Automating handwriting extraction, policy validation, and mathematical scrutiny using Agentic AI.")
st.divider()

# --- SIDEBAR NAV ---
st.sidebar.header("📁 Navigation Menu")
choice = st.sidebar.radio(
    "Select Functionality:",
    ["1. Descriptive Papers (Theory)", "2. Bit Paper Scrutiny (MCQ)", "3. Total Marks Scrutiny (Award Sheet)"]
)

# Ensure base directories exist cleanly
Path("data/pdf_files").mkdir(parents=True, exist_ok=True)
Path("data/bit/pdf_files").mkdir(parents=True, exist_ok=True)
Path("data/award_sheet/process").mkdir(parents=True, exist_ok=True)

# --- WORKFLOW 1: DESCRIPTIVE PAPERS ---
if choice == "1. Descriptive Papers (Theory)":
    st.header("📝 Descriptive Papers Evaluation")
    st.caption("Processes evaluation front pages, applies Best-of-N section logic, and formats reports.")
    
    uploaded_file = st.file_uploader("Upload Scanned Theory Exam PDF", type=["pdf"])
    
    if uploaded_file is not None:
        save_path = Path("data/pdf_files") / "theory_input.pdf"
        
        # Stream raw chunks cleanly without blocking the UI main thread loop
        try:
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"📦 '{uploaded_file.name}' successfully staged in directory.")
        except Exception as file_err:
            st.error(f"Failed to write file to disk storage array: {file_err}")
            
        st.divider()
        
        # Process trigger engine button
        if st.button("🚀 Run Evaluation Pipeline", type="primary"):
            # Put the heavy loader context exactly where the deep computing execution takes place
            with st.spinner("⚙️ Executing Agentic Pipeline... Converting pages, calling Gemini Vision APIs, and validating marks. Please do not close this tab."):
                run_full_pipeline()
            st.success("🏁 Execution completed successfully!")
            
            # Read latest execution datasets
            report_dir = Path("data/reports")
            result_files = list(report_dir.glob("exam_results_*.csv"))
            fail_files = list(report_dir.glob("failed_students_*.csv"))
            
            st.divider()
            tab1, tab2 = st.tabs(["📊 Successfully Extracted Results", "⚠️ Audit Failures & System Logs"])
            
            with tab1:
                if result_files:
                    latest_result = max(result_files, key=os.path.getmtime)
                    df_results = pd.read_csv(latest_result)
                    st.subheader(f"Extracted Records ({latest_result.name})")
                    st.dataframe(df_results, use_container_width=True)
                else:
                    st.info("No successful exam results generated in this batch run.")
                    
            with tab2:
                if fail_files:
                    latest_fail = max(fail_files, key=os.path.getmtime)
                    df_fails = pd.read_csv(latest_fail)
                    st.subheader(f"Flagged Anomalies ({latest_fail.name})")
                    st.warning("The following records failed mathematical rule checks or experienced extraction limits:")
                    st.dataframe(df_fails, use_container_width=True)
                else:
                    st.success("✅ Clean Audit Trail! No student records failed validation rules in this batch.")
# --- WORKFLOW 2: BIT PAPERS ---
elif choice == "2. Bit Paper Scrutiny (MCQ)":
    st.header("🎯 Bit Paper MCQ Grading")
    st.caption("Grades 20-bit handwritten options against a master key with cross-verification.")
    
    col1, col2 = st.columns(2)
    with col1:
        pages_per_student = st.selectbox("Pages per student layout:", [1, 2], index=1)
    with col2:
        master_key = st.text_input("Enter 20-Character Master Key (e.g. ABCD...):", max_chars=40)
        
    uploaded_file = st.file_uploader("Upload Scanned Bit Paper PDF", type=["pdf"])
    
    if uploaded_file is not None:
        save_path = Path("data/bit/pdf_files") / "bit_input.pdf"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Bit paper staged in inbox.")
        
        if st.button("🚀 Grade Papers", type="primary"):
            if not master_key or len(master_key.replace(" ", "").replace(",", "")) < 20:
                st.error("Please enter a valid 20-character faculty answer key before executing.")
            else:
                with st.spinner("Splitting identity boundaries and calculating grading metrics..."):
                    result = bit_orchestrator(no_pages=pages_per_student, raw_key_string=master_key)
                
                if result.get("status") == "Success":
                    st.success("Grading complete!")
                    if result.get("success_report") and os.path.exists(result["success_report"]):
                        st.subheader("📊 Graded Records Table")
                        st.dataframe(pd.read_csv(result["success_report"]), width=True)
                else:
                    st.error(f"Pipeline error: {result.get('message')}")

# --- WORKFLOW 3: AWARD SHEET SCRUTINY ---
elif choice == "3. Total Marks Scrutiny (Award Sheet)":
    st.header("📊 Final Marks Award Sheet Scrutiny")
    st.caption("Cross-references Descriptive (15M) + Bit Paper (10M) + Activity (5M) equal to the posted summary column.")
    
    uploaded_image = st.file_uploader("Upload Scanned Award Sheet Image", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        # Secure the actual filename to maintain audit lineage
        actual_filename = uploaded_image.name
        save_dir = Path("data/award_sheet/process")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct path using the actual uploaded filename
        local_image_path = save_dir / actual_filename
        
        # 1. Write the file completely to disk under its true lineage name
        with open(local_image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
            
        # 2. Store the path in session state so Streamlit doesn't lose it on button clicks
        st.session_state["current_award_sheet"] = str(local_image_path)
        
        st.divider()
        
        # Create a stable layout structure
        col_img, col_metrics = st.columns([1, 1])
        
        # 3. LOAD PREVIEW DIRECTLY FROM STATIC STORAGE
        with col_img:
            st.subheader("🖼️ Uploaded Sheet Viewer")
            saved_path_str = st.session_state.get("current_award_sheet")
            
            if saved_path_str and os.path.exists(saved_path_str):
                # Using the PIL Image approach to guarantee render safety
                img_to_show = Image.open(saved_path_str)
                st.image(img_to_show, use_container_width=True, caption=f"Lineage Trace: {actual_filename}")
            else:
                st.error("Target storage path failed to synchronize binary content.")
            
        # 4. COMPUTATION SIDEBAR
        # --- Inside streamlit_app.py -> Choice 3 column 2 ---
        with col_metrics:
            st.subheader("🔍 Automated Audit Control")
            st.info(f"📋 Staged for processing: `{actual_filename}`")
            
            if st.button("🔎 Execute Sum Verification Check", type="primary"):
                with st.spinner("🤖 Gemini Vision Agent is analyzing the matrix structure and verifying sums..."):
                    # Call our newly updated backend function
                    errors_list = run_scrutiny() 
                
                st.subheader("📋 Audit Report Summary")
                
                # Check if the returned list is completely empty (No errors found)
                if not errors_list:
                    st.success("✅ *Scrutiny Complete:* All student totals match perfectly on this sheet!")
                
                # Check if a system/API string exception was returned instead of a list
                elif isinstance(errors_list, str):
                    st.error(f"System Exception: {errors_list}")
                    
                # If discrepancies are located, render the custom interactive grid
                else:
                    st.error(f"🚨 Located {len(errors_list)} Mathematical Addition Mismatches!")
                    st.markdown("Review the flagged discrepancies below to trace human calculation errors:")
                    
                    # Convert the array to a Pandas Dataframe cleanly
                    df_errors = pd.DataFrame(errors_list)
                    
                    # Apply a custom background styling trick to highlight the wrong total column in light red
                    def highlight_mismatch(val):
                        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'

                    styled_df = df_errors.style.applymap(
                        highlight_mismatch, 
                        subset=["Calculated Sum", "Faculty Posted Total"]
                    )
                    
                    # Display the styled interactive data sheet on screen
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Quick reference stats summary cards
                    st.divider()
                    st.caption("💡 *Quick Action Triage:* Filter the table above by clicking any column header to locate the largest error margins first.")