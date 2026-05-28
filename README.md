# AI Exam Auditor 📝🤖

An automated pipeline for extracting, validating, and auditing student marks from handwritten exam front pages. This tool is designed to eliminate manual data entry errors and ensure "Best-of-N" academic rules are followed with 100% mathematical accuracy.

## 🚀 The Pipeline
This project implements a professional **Ingestion Pattern** to handle batch processing:
1. **Inbox**: Drop your scanned exam PDFs into `data/pdf_files/`.
2. **Split**: The system converts PDFs into optimized 150 DPI images in `data/process/`.
3. **AI Extraction**: Gemini 2.5 Flash reads handwritten marks into structured data.
4. **Validation**: Institutional rules are applied (e.g., Section Best-of-2 logic).
5. **Archive**: Processed images move to `success/` or `error/`, and original PDFs move to `archive_pdfs/`.
6. **Report**: A timestamped CSV is generated in `data/reports/` with a full audit trail.

## 📁 Project Structure
```text
exam-marks-extractor/
├── data/
│   ├── pdf_files/      # Inbox: Drop new exam PDFs here
│   ├── process/        # Landing Zone: Temporary JPGs
│   ├── success/        # Archive: Validated student images
│   ├── error/          # Review: Images requiring manual check
│   ├── archive_pdfs/   # Archive: Original PDFs after splitting
│   └── reports/        # Output: Timestamped CSV results
├── extractor.py        # Gemini Vision & Pydantic schemas
├── validator.py        # Best-of logic and math validation
├── pdf_splitter.py     # PDF to optimized image converter
├── batch_processor.py  # Orchestration & folder management
├── pipeline.py         # Master script to run the full sequence
├── .env                # API Keys & Poppler Path (Git Ignored)
└── requirements.txt    # Python dependencies
```
## 🎓 Agentic Bit-Paper Evaluator
An AI-powered grading agent that automates the evaluation of handwritten multiple-choice (Bit) papers. The system uses computer vision to extract student IDs, validates AI-calculated marks against faculty handwritten totals, and generates detailed lineage reports.

## 🚀 Features
Automated PDF Splitting: FIFO-based processing that groups PDF pages into individual student identities.

Vision-Agent Intelligence: Powered by Gemini 2.5 Flash via LangChain to read messy handwriting and strikethroughs.

Faculty Validation Loop: Automatically flags discrepancies if the AI's calculation doesn't match the teacher's handwritten marks.

WhatsApp-Ready Architecture: Designed for a conversational UI where faculty can upload files and provide answer keys on the go.

Robust Reporting: Generates student-wise CSVs for every PDF and a master error report for audit trails.

## 📂 Project Structure
Plaintext
marks-extractor-project/
├── data/
│   └── bit/
│       ├── pdf_files/      # Inbox for new exam PDFs
│       ├── process/        # Temporary storage for extracted images
│       ├── success/        # Validated student images
│       ├── error/          # Discrepancy/Failed images for review
│       └── reports/        # Generated CSV results and error logs
├── bit_pdf_splitter.py     # PDF to Image conversion & lineage naming
├── bit_evaluator.py        # AI Grading & Faculty Validation logic
├── bit_pipeline.py         # Orchestrator for the end-to-end workflow
└── .env                    # API keys and environment variables
## ⚙️ Installation
Clone the repository:

```Bash
git clone https://github.com/yourusername/bit-paper-evaluator.git
cd bit-paper-evaluator
Install Dependencies:
```
```Bash
pip install langchain-google-genai pandas pdf2image python-dotenv pydantic pillow
```
## Install Poppler (for PDF processing):

Ensure poppler is installed and the path is added to your environment variables or .env file.

## Setup Environment Variables:
Create a .env file in the root directory:

```Code snippet
GEMINI_API_KEY=your_api_key_here
POPPLER_PATH=C:/path/to/poppler/bin
```
## 🛠️ Usage
Running the Pipeline
To process all PDFs in the pdf_files folder:

```Bash
python bit_pipeline.py
```
## The Workflow
Upload: Place your scanned bit-papers in data/bit/pdf_files/.
Split: The system detects the oldest PDF and splits it based on no_pages per student.

Grade: The AI reads the student registration number and 20 answers.

Validate: The system compares the calculated score (0.5 per bit) against the faculty's total.

Report: CSVs are generated in data/bit/reports/ with full data lineage.

https://agentic-exam-auditor.streamlit.app/