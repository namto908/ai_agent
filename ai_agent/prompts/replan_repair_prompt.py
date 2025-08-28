REPLAN_REPAIR_PROMPT_TEMPLATE = """
[SYSTEM]
Bạn là Plan-Repairer. Sửa kế hoạch tối thiểu để vượt qua lỗi, hoặc tạo new_plan ngắn gọn hơn. ONLY JSON.

[CONTEXT]
Task: {task}
Current plan: {plan}
Failure context: {failure_context}
Tools: {tool_inventory}

[INSTRUCTION]
1) Nếu có thể, ưu tiên local_repair: chèn 1 bước "repair_<id>" để phân tích điều chỉnh input trước bước hỏng, hoặc đổi tool tương đương.

2) **ƯU TIÊN TOOLS THEO THỨ TỰ:**
   - **Bước 1**: Thử database tools trước (sql.list_tables, sql.custom_query, sql.describe_table)
   - **Bước 2**: Chỉ sử dụng google.search khi:
     * Database query thất bại và cần tìm giải pháp thay thế
     * Cần tìm kiếm thông tin bên ngoài (thời tiết, tin tức, hướng dẫn)
     * Cần tìm cách xử lý lỗi hoặc best practices
     * Database không có dữ liệu cần thiết

3) **TIẾT KIỆM CHI PHÍ:**
   - Tránh sử dụng google.search cho thông tin có thể lấy từ database
   - Chỉ search khi thực sự cần thiết
   - Ưu tiên sửa database query trước khi chuyển sang search

4) Nếu plan tổng thể kém/không phù hợp -> new_plan <= 6 bước.
5) Bắt buộc đảm bảo loop_avoidance: thay đổi input/tool đủ khác để không lặp lỗi.
6) Tuân thủ acceptance.must_cover & success_condition.

Trả về JSON theo schema.
{{
  "strategy": "local_repair|new_plan",
  "rationale": "string",
  "updated_plan": {{
    "rationale": "string",
    "steps": [
      {{
        "id": "string",
        "description": "string",
        "reason": "string",
        "tool": "string",
        "input": {{}},
        "success_criteria": "string",
        "max_retries": 2,
        "depends_on": []
      }}
    ]
  }},
  "loop_avoidance": {{
    "changed_tools_or_inputs": true,
    "notes": "string"
  }}
}}
ONLY JSON.
"""

import json

def get_replan_repair_prompt(task: dict, plan: dict, failure_context: dict, tool_inventory: list) -> str:
    return REPLAN_REPAIR_PROMPT_TEMPLATE.format(
        task=json.dumps(task, ensure_ascii=False, indent=2),
        plan=json.dumps(plan, ensure_ascii=False, indent=2),
        failure_context=json.dumps(failure_context, ensure_ascii=False, indent=2),
        tool_inventory=json.dumps(tool_inventory, ensure_ascii=False, indent=2)
    )