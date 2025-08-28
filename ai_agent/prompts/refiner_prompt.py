"""
Prompt for the Refiner node.
"""

# C) Refiner Prompt
REFINER_PROMPT_TEMPLATE = """
Khi bước "{step_title}" thất bại với lỗi "{error}", hãy sửa tối thiểu phần input để tăng khả năng đạt expect.

**Step hiện tại:**
- Action: {action}
- Input: {input}
- Expect: {expect}
- Retries còn lại: {retries_left}

**Chiến lược gợi ý:**
- KG: đổi/tách từ khóa, điều chỉnh params, tăng LIMIT hợp lý.
- RAG: tăng top_k (≤ 15), thêm đồng nghĩa, ràng buộc chủ đề.
- HTTP: tăng timeout, chọn URL mirror (nếu có trong whitelist).

Không thay đổi action. Không phá vỡ enum. Không thêm bước mới.
Chỉ trả về JSON object chứa phần input mới.

**Input mới (chỉ phần thay đổi):**
"""

def get_refiner_prompt(step: dict, error: str, retries_left: int) -> str:
    return REFINER_PROMPT_TEMPLATE.format(
        step_title=step.get('title'),
        error=error,
        action=step.get('action'),
        input=step.get('input'),
        expect=step.get('expect'),
        retries_left=retries_left
    )
