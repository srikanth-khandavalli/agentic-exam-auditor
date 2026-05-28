import os
import time
import shutil
import datetime
import pandas as pd
from extractor import extract_marks_from_image
from validator import validate_exam_marks

def process_all_exams():
    base_dir = "data"
    process_dir = os.path.join(base_dir, "process")
    success_dir = os.path.join(base_dir, "success")
    error_dir = os.path.join(base_dir, "error")
    reports_dir = os.path.join(base_dir, "reports")

    for d in [success_dir, error_dir, reports_dir]:
        os.makedirs(d, exist_ok=True)

    all_results = []
    failed_log = [] # <--- NEW: List to track failures
    files = [f for f in os.listdir(process_dir) if f.lower().endswith(('.jpg', '.jpeg'))]
    
    if not files:
        print("📭 No files found in 'process' folder.")
        return

    print(f"📂 Processing {len(files)} files...")

    for filename in files:
        source_path = os.path.join(process_dir, filename)
        
        try:
            # 1. ATTEMPT EXTRACTION
            raw_data = extract_marks_from_image(source_path)
            data_dict = raw_data.model_dump()
            validation = validate_exam_marks(data_dict)
            
            # 2. VALIDATION CHECK
            if validation["is_valid"]:
                # Calculation logic for the final report
                b12 = max(data_dict['q1']['row_total'], data_dict['q2']['row_total'])
                b34 = max(data_dict['q3']['row_total'], data_dict['q4']['row_total'])
                b56 = max(data_dict['q5']['row_total'], data_dict['q6']['row_total'])

                row = {
                    "Source_File": filename,
                    "Reg_No": data_dict["registration_number"],
                    "Total_Written": data_dict["total_marks_written"],
                    "Scaled_Marks": data_dict["scaled_marks"],
                    "best_1_2": b12, "best_3_4": b34, "best_5_6": b56
                }
                
                for i in range(1, 7):
                    q_data = data_dict[f"q{i}"]
                    for sub in ['a', 'b', 'c', 'd', 'row_total']:
                        row[f"Q{i}_{sub}"] = q_data[sub]
                
                all_results.append(row)
                
                # Move to SUCCESS only if extraction AND validation pass
                shutil.move(source_path, os.path.join(success_dir, filename))
                print(f"✅ {filename} -> Success")
            else:
                # PERMANENT ERROR: Move to error folder (e.g., bad math or data)
                shutil.move(source_path, os.path.join(error_dir, filename))
                print(f"❌ {filename} -> Validation Error: {validation['message']}")
                # Track VALIDATION failure
                failed_log.append({"File_Name": filename, "Error_Type": "Validation", "Reason": validation["message"]})

        except Exception as e:
            # 3. TEMPORARY API ERROR (Rate Limit)
            # Check for common rate limit strings for both Gemini and OpenAI
            if any(msg in str(e).lower() for msg in ["429", "resourceexhausted", "rate_limit", "insufficient_quota"]):
                print(f"⛔ Quota hit at {filename}. STALLING loop to save progress...")
                # CRITICAL: We 'break' here WITHOUT moving the file.
                # It stays in 'process' so it can be picked up in the next run.
                failed_log.append({"File_Name": filename, "Error_Type": "System/API", "Reason": str(e)})
                break 
            elif any(msg in str(e).lower() for msg in ["503", "unavailable", "please try again later"]):
                print(f"⚠️ LLM server busy to process {filename}. retrying after 5 seconds...")
                # We 'continue' here WITHOUT moving the file.
                # It stays in 'process' so it can be retried in the next loop iteration
                failed_log.append({"File_Name": filename, "Error_Type": "System/API", "Reason": str(e)})
                time.sleep(5)
                continue
            else:
                # 4. OTHER SYSTEM ERRORS (Actual code crashes)
                print(f"⚠️ {filename} -> System Error: {str(e)}")
                shutil.move(source_path, os.path.join(error_dir, filename))
                # Track SYSTEM/API failure
                failed_log.append({"File_Name": filename, "Error_Type": "System/API", "Reason": str(e)})
                continue

        # Respect a short cooldown for the Paid Tier (e.g., OpenAI)
        # Change back to 60 if using Gemini Free Tier
        time.sleep(1) 

    # 1. Save any results accumulated before a potential break
    if all_results:
        df = pd.DataFrame(all_results)
        df = df.sort_values(by="Reg_No")
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(reports_dir, f"exam_results_{now}.csv")
        df.to_csv(output_path, index=False)
        print(f"\n📊 Batch complete! Report saved to: {output_path}")
    # 2. Save failed students log
    if failed_log:
        df_failed = pd.DataFrame(failed_log)
        df_failed.to_csv(os.path.join(reports_dir, f"failed_log_{now}.csv"), index=False)
        print(f"\n📑 {len(failed_log)} students failed. See failed_log_{now}.csv for details.")
if __name__ == "__main__":
    process_all_exams()