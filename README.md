# 🤖 AI Agent Project

Một AI Agent thông minh được xây dựng với LangGraph, hỗ trợ đa database (PostgreSQL, Milvus, Neo4j) và hệ thống memory management.

## 🌟 Tính năng chính

### 🧠 **AI Agent Architecture**
- **Plan-Act-Reflect Pattern**: Sử dụng LangGraph để tạo workflow thông minh
- **Multi-LLM Support**: Hỗ trợ DeepSeek, OpenAI, Anthropic, Google Gemini
- **Intent Classification**: Tự động phân loại ý định người dùng
- **Cost Optimization**: Ưu tiên database tools, giảm thiểu Google Search API

### 🗄️ **Database Integration**
- **PostgreSQL**: Truy vấn SQL, liệt kê bảng, mô tả schema
- **Milvus**: Vector database, liệt kê collections, search embeddings
- **Neo4j**: Graph database, truy vấn Cypher, phân tích relationships
- **Database Differentiation**: Tự động phân biệt và chọn tool phù hợp

### 💾 **Memory Management**
- **Short-term Memory**: In-memory cho session hiện tại
- **Long-term Memory**: SQLite database với full-text search
- **Memory Context**: Tự động tìm và hiển thị câu hỏi tương tự
- **User Statistics**: Thống kê tương tác, success rate, common intents

### 🎨 **User Interface**
- **Streamlit Web App**: Giao diện web thân thiện
- **Dark Theme**: Giao diện tối dễ nhìn
- **Expandable Sections**: Hiển thị nội dung dài
- **Memory Management UI**: Thống kê, xóa, xuất memory

## 🚀 Cài đặt

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai_agent_project
```

### 2. Tạo Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Cài đặt Dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình Environment
Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
```

Cấu hình các biến môi trường:
```env
# LLM Configuration
LLM_PROVIDER=deepseek  # deepseek, openai, anthropic, gemini, custom
LLM_API_KEY=your_api_key
LLM_API_URL=https://api.deepseek.com/v1  # Optional for custom
LLM_MODEL_ID=deepseek-chat  # Model name

# Database Configuration
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=your_username
MILVUS_PASSWORD=your_password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Google Search API (Optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
```

## 🎯 Sử dụng

### 1. Chạy Streamlit App
```bash
streamlit run streamlit_app.py
```

Truy cập: http://localhost:8501

### 2. Sử dụng Command Line
```bash
python main.py
```

### 3. Ví dụ sử dụng

#### Database Queries
```python
# PostgreSQL
"Liệt kê các bảng trong PostgreSQL"
"Mô tả cấu trúc bảng users"
"Truy vấn SELECT * FROM users LIMIT 10"

# Milvus
"Liệt kê các collection trong Milvus"
"Mô tả index của collection demo_collection"
"Tìm kiếm vector tương tự trong collection"

# Neo4j
"Truy vấn graph trong Neo4j"
"Tìm các node có label Person"
"Phân tích relationships trong graph"
```

#### General Queries
```python
"Xin chào"
"Thời tiết hôm nay tại Hà Nội"
"Tìm kiếm thông tin về Python"
```

## 🏗️ Kiến trúc

### 📁 Cấu trúc Project
```
ai_agent_project/
├── ai_agent/
│   ├── __init__.py
│   ├── graph.py              # LangGraph workflow
│   ├── state.py              # Pydantic models
│   ├── llm_client.py         # Multi-LLM client
│   ├── memory.py             # Memory management
│   ├── nodes/                # Workflow nodes
│   │   ├── router.py         # Intent classification
│   │   ├── intent_extraction.py
│   │   ├── planner.py        # Plan generation
│   │   ├── executor.py       # Action execution
│   │   ├── reflection.py     # Result evaluation
│   │   ├── synthesizer.py    # Final answer
│   │   ├── memory_handler.py # Memory operations
│   │   └── ...
│   ├── prompts/              # LLM prompts
│   │   ├── system_prompts.py
│   │   ├── router_prompt.py
│   │   ├── plan_generation_prompt.py
│   │   └── ...
│   └── tools/                # Database tools
│       ├── database.py       # PostgreSQL
│       ├── rag.py           # Milvus
│       ├── knowledge_graph.py # Neo4j
│       └── ...
├── streamlit_app.py          # Web interface
├── main.py                   # CLI interface
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

### 🔄 Workflow
```
User Input → Router → Intent Extraction → Memory Handler → 
Plan Generation → Action Execution → Reflection → 
Final Synthesis → Memory Storage → Response
```

## 🛠️ Development

### Testing
```bash
# Run tests
pytest

# Test specific components
python -c "from ai_agent.graph import build_graph; agent = build_graph(); print('✅ Agent loaded successfully')"
```

### Code Formatting
```bash
# Format code
black ai_agent/

# Lint code
flake8 ai_agent/
```

### Adding New Tools
1. Tạo tool trong `ai_agent/tools/`
2. Thêm action vào `Action` enum trong `state.py`
3. Cập nhật executor mapping
4. Thêm tool card vào system prompts

## 🔧 Cấu hình LLM

### DeepSeek
```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your_deepseek_api_key
LLM_MODEL_ID=deepseek-chat
```

### OpenAI
```env
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL_ID=gpt-4
```

### Anthropic
```env
LLM_PROVIDER=anthropic
LLM_API_KEY=your_anthropic_api_key
LLM_MODEL_ID=claude-3-sonnet-20240229
```

### Google Gemini
```env
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key
LLM_MODEL_ID=gemini-pro
```

## 📊 Memory Management

### Memory Features
- **Session-based**: Lưu trữ theo session và user
- **Full-text Search**: Tìm kiếm câu hỏi tương tự
- **Statistics**: Thống kê tương tác, success rate
- **Export**: Xuất memory ra JSON

### Memory Operations
```python
# Trong Streamlit UI
- 📊 Thống kê: Xem user statistics
- 🗑️ Xóa Memory: Clear user memory
- 📤 Xuất Memory: Export to JSON
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection
```bash
# Kiểm tra PostgreSQL
psql -h localhost -U username -d database

# Kiểm tra Milvus
python -c "from pymilvus import connections; connections.connect('default', host='localhost', port='19530')"

# Kiểm tra Neo4j
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))"
```

#### 2. LLM API Issues
```bash
# Test LLM connection
python -c "from ai_agent.llm_client import get_llm_client; client = get_llm_client(); print('✅ LLM connected')"
```

#### 3. Memory Database
```bash
# Kiểm tra SQLite memory
python -c "import sqlite3; conn = sqlite3.connect('memory.db'); print('✅ Memory DB accessible')"
```

## 📈 Performance

### Optimization Tips
1. **Use Database Tools**: Ưu tiên database queries thay vì Google Search
2. **Memory Context**: Tận dụng memory để tránh lặp lại
3. **Batch Operations**: Xử lý nhiều queries cùng lúc
4. **Connection Pooling**: Tái sử dụng database connections

### Monitoring
- **Latency**: Theo dõi thời gian phản hồi
- **Success Rate**: Tỷ lệ thành công của queries
- **Memory Usage**: Sử dụng memory database
- **API Costs**: Chi phí Google Search API

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 🙏 Acknowledgments

- **LangGraph**: Framework cho AI workflows
- **Streamlit**: Web interface framework
- **Pydantic**: Data validation
- **Database Drivers**: PostgreSQL, Milvus, Neo4j

---

**Made with ❤️ by AI Agent Team**
