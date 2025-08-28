FINAL_SYNTHESIS_PROMPT_TEMPLATE = """
[SYSTEM]
Bạn là Synthesizer. Xuất kết quả cuối cùng đúng định dạng và đúng acceptance. 

[CONTEXT]
Acceptance: {acceptance}
Plan (final): {plan}
Observations: {observations}
Format hints: {format_hints}

[INSTRUCTION]
1) Kiểm tra đủ "must_cover" và "success_condition".
2) Nếu deliverable_format = "markdown": 
   - Trả Markdown sạch, có tiêu đề, mục gạch đầu dòng ngắn.
   - Kèm mục "Bằng chứng", "Giới hạn" (nếu có).
   - Nếu có dữ liệu có cấu trúc (danh sách, bảng), sử dụng Markdown tables để hiển thị.
   - Ví dụ: | Cột 1 | Cột 2 | Cột 3 |
           |-------|-------|-------|
           | Dữ liệu 1 | Dữ liệu 2 | Dữ liệu 3 |
3) Nếu deliverable_format = "json" hoặc "custom:<name>":
   - Trả JSON đúng schema yêu cầu. Nếu không có schema riêng, dùng schema chung.
4) Không lộ thông tin nhạy cảm/PII.

[OUTPUT]
Trả đúng theo deliverable_format (Markdown hoặc JSON). Không kèm giải thích thừa.
"""

import json

def get_final_synthesis_prompt(acceptance: dict, plan: dict, observations: list, format_hints: dict) -> str:
    return FINAL_SYNTHESIS_PROMPT_TEMPLATE.format(
        acceptance=json.dumps(acceptance, ensure_ascii=False, indent=2),
        plan=json.dumps(plan, ensure_ascii=False, indent=2),
        observations=json.dumps(observations, ensure_ascii=False, indent=2),
        format_hints=json.dumps(format_hints, ensure_ascii=False, indent=2)
    )