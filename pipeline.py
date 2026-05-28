import os
import time
from pdf_splitter import split_all_pdfs
from batch_processor import process_all_exams

def run_full_pipeline():
    print("="*50)
    print("🚀 STARTING EXAM DATA EXTRACTION PIPELINE")
    print("="*50)
    
    start_time = time.time()

    # STEP 1: Split PDFs into the Landing Zone
    print("\n[PHASE 1] Splitting PDFs...")
    split_all_pdfs()
    
    # STEP 2: Process the images through Gemini
    print("\n[PHASE 2] Extracting Marks & Validating...")
    process_all_exams()

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    print("\n" + "="*50)
    print(f"🏁 PIPELINE COMPLETE in {duration} seconds.")
    print("Check 'data/reports' for your final CSV.")
    print("Check 'data/error' for any papers that need manual review.")
    print("="*50)

def run_chunked_pipeline():
    # 1. Run the splitter (DPI 90 is recommended now)
    from pdf_splitter import split_all_pdfs
    split_all_pdfs()

    # 2. Process in chunks to respect TPM limits
    from batch_processor import process_all_exams
    
    # We will loop and run the processor multiple times 
    # Because your code moves files to /success, it will only
    # pick up what's left in /process each time.
    
    while True:
        files_remaining = len([f for f in os.listdir("data/process") if f.lower().endswith(('.jpg', '.jpeg'))])
        
        if files_remaining == 0:
            print("🏁 All students processed!")
            break
            
        print(f"\n🚀 Processing next batch. {files_remaining} students left...")
        process_all_exams() # This script handles its own 20s sleep between files
        
        # If the script breaks due to 429, wait 60 seconds before the next loop
        print("⏳ Waiting... attempting to reprocess remaining files. ctrl+c to stop.")
        time.sleep(1)

if __name__ == "__main__":
    run_chunked_pipeline()

# if __name__ == "__main__":
#     run_full_pipeline()