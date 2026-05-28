import os
import shutil  # Required for moving files
from pathlib import Path
from pdf2image import convert_from_path
# from dotenv import load_dotenv

# load_dotenv()

def get_oldest_pdf(input_dir):
    """Finds the oldest created PDF file in the specified directory."""
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if not pdf_files:
        return None
    # Sort by creation time (FIFO)
    pdf_files.sort(key=lambda x: os.path.getctime(x))
    return pdf_files[0]

def bit_pdf_splitter(no_pages=2):
    base_dir = Path("data/bit")
    input_dir = base_dir / "pdf_files"
    output_dir = base_dir / "process"
    archive_dir = base_dir / "archived_pdfs" # Added archive location
    
    # Ensure directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 1. Identify only the oldest PDF
    pdf_path = get_oldest_pdf(input_dir)
    
    if not pdf_path:
        print("No PDF files found in bit/pdf_files.")
        return None

    poppler_bin = os.getenv("POPPLER_PATH")
    pdf_stem = pdf_path.stem.replace(" ", "_")

    try:
        print(f"Processing oldest file: {pdf_path.name}")
        pages = convert_from_path(pdf_path, dpi=150, poppler_path=poppler_bin)

        student_count = 1
        for i in range(0, len(pages), no_pages):
            for p_idx in range(no_pages):
                actual_idx = i + p_idx
                if actual_idx < len(pages):
                    page_image = pages[actual_idx]
                    filename = f"{pdf_stem}_S{student_count}_P{p_idx + 1}.jpg"
                    page_image.save(output_dir / filename, "JPEG")
                    print(f"Generated: {filename}")
            student_count += 1
            
        print(f"Successfully split {pdf_path.name}")

        # --- ARCHIVING LOGIC STARTS HERE ---
        # Move the file only after successful splitting
        dest_path = archive_dir / pdf_path.name
        
        # If a file with the same name exists in archive, remove it first
        if dest_path.exists():
            os.remove(dest_path)
            
        shutil.move(str(pdf_path), str(dest_path))
        print(f"Archived {pdf_path.name} to {archive_dir}")
        # --- ARCHIVING LOGIC ENDS HERE ---

        return pdf_path

    except Exception as e:
        print(f"Failed to split {pdf_path.name}: {e}")
        return None

if __name__ == "__main__":
    bit_pdf_splitter(no_pages=2)