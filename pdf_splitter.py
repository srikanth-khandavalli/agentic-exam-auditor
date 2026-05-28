import os
import glob
import shutil
from pdf2image import convert_from_path
# from dotenv import load_dotenv

# load_dotenv()
import streamlit as st

try:
    poppler_bin = st.secrets.get("POPPLER_PATH", os.getenv("POPPLER_PATH"))
except Exception:
    poppler_bin = os.getenv("POPPLER_PATH")

# Clean the path string (if it's empty or blank string "", convert it to None so pdf2image uses system path)
if not poppler_bin or str(poppler_bin).strip() == "":
    poppler_bin = None

def split_all_pdfs(input_dir="data/pdf_files", output_dir="data/process", archive_dir="data/archive_pdfs"):
    # 1. Folder Setup
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    
    poppler_bin = os.getenv("POPPLER_PATH")
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"📭 No new PDF files found in {input_dir}")
        return

    print(f"🚀 Found {len(pdf_files)} PDF(s) to process.")
    print("-" * 30)

    for pdf_path in pdf_files:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"📄 Opening: {base_name}.pdf")
        
        try:
            # Convert PDF to Images
            pages = convert_from_path(pdf_path, dpi=90, poppler_path=poppler_bin)
            total_pages = len(pages)
            print(f"   🔢 Found {total_pages} pages. Splitting now...")

            for i, page in enumerate(pages):
                image_name = f"{base_name}_page_{i+1}.jpg"
                save_path = os.path.join(output_dir, image_name)
                
                # Save the image
                page.save(save_path, "JPEG")
                
                # THIS IS THE PROGRESS MESSAGE YOU WANTED:
                print(f"   [Page {i+1}/{total_pages}] ✅ Saved: {image_name}")
            
            # Archive the PDF
            shutil.move(pdf_path, os.path.join(archive_dir, f"{base_name}.pdf"))
            print(f"✨ Finished {base_name}.pdf and moved to Archive.\n")
                
        except Exception as e:
            print(f"❌ Error converting {pdf_path}: {str(e)}")

    print("-" * 30)
    print("🏁 All PDF splitting tasks complete!")

if __name__ == "__main__":
    split_all_pdfs()