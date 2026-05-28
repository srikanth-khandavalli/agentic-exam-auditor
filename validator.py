import re

def validate_exam_marks(data: dict) -> dict:
    reg_no = data.get("registration_number", "")
    if not re.match(r"^\d{2}[a-zA-Z]", reg_no):
        return {"is_valid": False, "message": f"Invalid Reg No: {reg_no}"}

    section_scores = {1: 0, 2: 0, 3: 0}
    
    for i in range(1, 7):
        q_key = f"q{i}"
        q_data = data.get(q_key, {})
        
        a, b, c, d = q_data.get('a', 0), q_data.get('b', 0), q_data.get('c', 0), q_data.get('d', 0)
        row_total = q_data.get('row_total', 0)
        
        if row_total > 10:
            return {"is_valid": False, "message": f"Q{i} total {row_total} exceeds 10."}
        
        if (a + b + c + d) > row_total:
            return {"is_valid": False, "message": f"Q{i} sub-marks sum to {a+b+c+d}, but total is {row_total}."}
        
        # Best-of logic: Section 1 (Q1,Q2), Section 2 (Q3,Q4), Section 3 (Q5,Q6)
        section_idx = (i - 1) // 2 + 1
        section_scores[section_idx] = max(section_scores[section_idx], row_total)

    calc_grand_total = sum(section_scores.values())
    written_total = data.get("total_marks_written", 0)

    if calc_grand_total != written_total:
        return {"is_valid": False, "message": f"Total mismatch! Calculated {calc_grand_total}, but written {written_total}."}

    return {"is_valid": True, "validated_total": calc_grand_total, "message": "Passed"}