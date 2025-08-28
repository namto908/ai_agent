REFLECTION_PROMPT_TEMPLATE = """
[SYSTEM]
Bạn là Reflector. Đánh giá tiến độ và quyết định bước tiếp theo. ONLY JSON.

[CONTEXT]
Task (acceptance): {task_acceptance}
Plan (current step + remaining): {plan}
Observation (last): {last_observation}
Progress: {progress_summary}

[INSTRUCTION]
1) Kiểm tra last_observation có đáp ứng success_criteria của step hiện tại không.
2) Cập nhật acceptance_progress: must_cover đã/ chưa đạt.
3) Nếu chưa đạt:
   - Nếu lỗi có thể do input/tool -> đề xuất "retry_with_adjustment" + input_patch cụ thể, ngắn gọn.
   - Nếu step không còn cần thiết -> "skip" (nêu lý do).
   - Nếu kế hoạch có vấn đề cơ bản -> "replan".
4) Nếu toàn bộ acceptance đã đạt -> "done".
5) Điền evidence để minh chứng ngắn gọn.

Trả về JSON theo schema.
{{
  "status": "continue|retry_with_adjustment|skip|replan|done",
  "message": "string",
  "adjustment": {{
    "target_step_id": "string",
    "input_patch": {{}},
    "reason": "string"
  }},
  "evidence": ["string"],
  "acceptance_progress": {{
    "covered": ["string"],
    "missing": ["string"]
  }}
}}
ONLY JSON.
"""

import json

def get_reflection_prompt(task_acceptance: dict, plan: dict, last_observation: dict, progress_summary: dict) -> str:
    return REFLECTION_PROMPT_TEMPLATE.format(
        task_acceptance=json.dumps(task_acceptance, ensure_ascii=False, indent=2),
        plan=json.dumps(plan, ensure_ascii=False, indent=2),
        last_observation=json.dumps(last_observation, ensure_ascii=False, indent=2),
        progress_summary=json.dumps(progress_summary, ensure_ascii=False, indent=2)
    )