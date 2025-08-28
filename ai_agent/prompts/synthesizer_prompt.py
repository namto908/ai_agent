"""
Prompt for the Synthesizer node.
"""

# E) Synthesizer Prompt
SYNTHESIZER_PROMPT_TEMPLATE = """
Tổng hợp câu trả lời cuối cùng, mạch lạc và đầy đủ cho câu hỏi của người dùng.

**Câu hỏi gốc:**
"{question}"

**Bằng chứng đã thu thập (Evidence):**
---
{evidence_summary}
---

**Tóm tắt ngắn hội thoại trước đó (nếu có):**
{chat_brief}

**Yêu cầu:**
- Dựa hoàn toàn vào bằng chứng đã cho.
- Nêu rõ: nguồn nào (step/action) cung cấp thông tin gì.
- Giải thích hợp lý, tránh mâu thuẫn.
- Nếu thiếu dữ liệu cốt lõi để trả lời, hãy nói rõ "Không đủ thông tin để trả lời" thay vì suy diễn.
- Trả lời bằng tiếng Việt.
- Nếu bằng chứng là kết quả từ việc liệt kê bảng (db_introspection_tool), hãy trình bày danh sách bảng một cách gọn gàng, có thể nhóm theo schema nếu số lượng bảng lớn (> 20).
- Nếu bằng chứng là lỗi kết nối database (ví dụ: "NO_DSN", "CONN_FAIL"), hãy trả lời ngắn gọn: "Bạn muốn kết nối database nào (PG_DSN hoặc host/db/user)?"
- Nếu bằng chứng là lỗi quyền truy cập schema (ví dụ: "permission denied for schema"), hãy trả lời: "Không có quyền xem schema X. Mình có thể liệt kê những schema bạn truy cập được, hoặc bạn chỉ định schema khác."

**Câu trả lời cuối cùng:**
"""

def get_synthesizer_prompt(question: str, evidence: list, chat_history: list[dict] | None = None) -> str:
    evidence_summary = ""
    if not evidence:
        evidence_summary = "Không có bằng chứng nào được thu thập."
    else:
        for ev in evidence:
            evidence_summary += f"- Nguồn: {ev.step_title} ({ev.source_action.value})\n"
            evidence_summary += f"  Nội dung: {ev.preview}\n"
            evidence_summary += f"  Metrics: {ev.metrics}\n\n"

    chat_brief = "Không có."
    if chat_history:
        turns = chat_history[-6:]
        chat_brief = "\n".join([f"- {t.get('role')}: {t.get('content')}" for t in turns])

    return SYNTHESIZER_PROMPT_TEMPLATE.format(
        question=question,
        evidence_summary=evidence_summary.strip(),
        chat_brief=chat_brief
    )

