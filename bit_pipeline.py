import os
from pathlib import Path
from bit_pdf_splitter import bit_pdf_splitter
from bit_evaluator import run_evaluation

def bit_orchestrator(no_pages: int, raw_key_string: str):
    """
    Orchestrates the Bit Paper grading process.
    
    Args:
        no_pages (int): Pages per student (1 or 2).
        raw_key_string (str): The 20-character answer key provided by faculty.
        
    Returns:
        dict: Summary of processing results including report paths for UI delivery.
    """
    print("\n" + "="*50)
    print("🚀 WHATSAPP AGENTIC PIPELINE ACTIVATED")
    print("="*50)

    # 1. Split the oldest PDF in the inbox
    # This uses the no_pages variable to pair images correctly
    pdf_path = bit_pdf_splitter(no_pages=no_pages)

    if not pdf_path:
        print("❌ ERROR: No PDF found in data/bit/pdf_files.")
        return {"status": "Error", "message": "No PDF found in inbox."}

    pdf_stem = pdf_path.stem.replace(" ", "_")
    print(f"📑 PROCESSING: {pdf_path.name} ({no_pages} pages/student)")

    # 2. Run Evaluation with the Dynamic Key
    # This processes images in 'process/', validates, and moves to success/error
    success = run_evaluation(raw_key_string)

    if not success:
        print(f"❌ ERROR: Evaluation failed for {pdf_path.name}. Check logs.")
        return {"status": "Error", "message": "Evaluation failed. Check process folder."}

    # 3. Prepare Report Locations for the WhatsApp Bot
    reports_dir = Path("data/bit/reports")
    success_csv = reports_dir / f"{pdf_stem}.csv"
    error_csv = reports_dir / f"{pdf_stem}_error_report.csv"

    summary = {
        "status": "Success",
        "pdf_source": pdf_path.name,
        "success_report": str(success_csv) if success_csv.exists() else None,
        "error_report": str(error_csv) if error_csv.exists() else None,
    }

    print("\n" + "="*50)
    print("📊 TASK COMPLETE")
    print(f"Source: {summary['pdf_source']}")
    print(f"Report: {summary['success_report']}")
    print(f"Errors: {summary['error_report']}")
    print("="*50 + "\n")

    return summary

if __name__ == "__main__":
    # Example usage (This is what your Flask/WhatsApp bot will call)
    # The bot will capture '2' and 'BDB...' from the user messages
    results = bit_orchestrator(no_pages=2, raw_key_string="BDB CB BAB AB BCC DBBA AC")