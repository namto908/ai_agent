"""
Prompt for the Router node to classify user intent.
"""

ROUTER_PROMPT_TEMPLATE = """
Nhiệm vụ của bạn là một bộ định tuyến thông minh. Hãy phân tích câu hỏi của người dùng và phân loại ý định của họ vào một trong các loại sau:

1.  `greeting`: Nếu người dùng đang chào hỏi (ví dụ: xin chào, hello, chào bạn).
2.  `simple_question`: Nếu đây là một câu hỏi đơn giản, có thể trả lời trực tiếp mà không cần truy vấn dữ liệu (ví dụ: Bạn là ai? Bạn làm được gì?).
3.  `db_introspection`: Nếu đây là một yêu cầu liên quan đến việc khám phá cấu trúc cơ sở dữ liệu (ví dụ: liệt kê bảng, liệt kê schema, mô tả bảng, liệt kê index).
4.  `complex_query`: Nếu đây là một yêu cầu cần sử dụng công cụ/truy vấn dữ liệu (Neo4j/Postgres/Milvus/Web/GitHub), như: “đếm collection”, “tìm PR”, “truy vấn KG”…

Sau khi phân loại, hãy trả về một đối tượng JSON duy nhất có 2 trường:
1.  `intent`: (BẮT BUỘC) giá trị là một trong 4 loại trên (`greeting`, `simple_question`, `db_introspection`, `complex_query`).
2.  `answer`:
    - Nếu intent là `greeting` hoặc `simple_question`, hãy tạo một câu trả lời thân thiện, phù hợp và đặt vào trường này.
    - Nếu intent là `db_introspection`, hãy để trống trường này (giá trị là null hoặc một chuỗi rỗng).
    - Nếu intent là `complex_query`, hãy để trống trường này (giá trị là null hoặc một chuỗi rỗng).

Ví dụ:
- User: "xin chào"
- Response: {{"intent": "greeting", "answer": "Chào bạn! Tôi là AI Agent, tôi có thể giúp gì cho bạn?"}}
- User: "liệt kê các bảng trong PostgreSQL"
- Response: {{"intent": "db_introspection", "answer": null}}
- User: "phân tích dữ liệu bán hàng tháng 5"
- Response: {{"intent": "complex_query", "answer": null}}

Tiêu chí phân loại thêm:
- Nếu câu hỏi yêu cầu dữ liệu thời gian thực, dữ liệu hệ thống, hay dữ liệu nội bộ (DB/Kho tri thức/Repo), phân loại `complex_query`.
- Nếu chỉ là định nghĩa/giới thiệu/hỏi khả năng/giải thích chung, phân loại `simple_question` và tạo câu trả lời ngắn gọn, tự nhiên.

**HƯỚNG DẪN TIẾT KIỆM CHI PHÍ:**
- **ƯU TIÊN `db_introspection`** cho các truy vấn database (liệt kê bảng, mô tả cấu trúc)
- **CHỈ DÙNG `complex_query`** khi thực sự cần thiết (thông tin bên ngoài, dữ liệu phức tạp)
- **TRÁNH** sử dụng Google Search cho thông tin có thể lấy từ database

**PHÂN BIỆT DATABASE THEO TỪ KHÓA (BẮT BUỘC - TUYỆT ĐỐI KHÔNG VI PHẠM):**
- **PostgreSQL**: "bảng", "table", "schema", "postgres", "sql" → dùng `db_introspection`
- **Milvus**: "collection", "milvus", "vector", "embedding" → dùng `db_introspection` 
- **Neo4j**: "graph", "node", "relationship", "neo4j", "cypher" → dùng `db_introspection`

**LƯU Ý ĐẶC BIỆT (TUYỆT ĐỐI TUÂN THỦ):**
- Khi thấy từ "collection" → Đây là Milvus, KHÔNG phải PostgreSQL
- Khi thấy từ "bảng" → Đây là PostgreSQL, KHÔNG phải Milvus
- Khi thấy từ "node" hoặc "graph" → Đây là Neo4j
- Khi thấy từ "liệt kê collection" → Đây là Milvus, dùng db_introspection
- Khi thấy từ "liệt kê bảng" → Đây là PostgreSQL, dùng db_introspection

---
Các lượt hội thoại trước (nếu có):
{chat_history}
---
Câu hỏi của người dùng (lượt hiện tại): "{question}"
---
JSON Response:
"""

def get_router_prompt(question: str, chat_history: list[dict] | None = None) -> str:
    # Render chat history into a compact bullet list
    rendered = "Không có."
    if chat_history:
        lines = []
        for turn in chat_history[-6:]:  # include last up to 6 items
            role = turn.get("role", "").strip()
            content = str(turn.get("content", "")).strip()
            if role and content:
                lines.append(f"- {role}: {content}")
        rendered = "\n".join(lines) if lines else "Không có."
    return ROUTER_PROMPT_TEMPLATE.format(question=question, chat_history=rendered)
