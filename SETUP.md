# 🚀 AI Agent Project - Setup Guide

Hướng dẫn cài đặt và cấu hình chi tiết cho AI Agent Project.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8+ (khuyến nghị 3.11+)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Storage**: 2GB+ free space
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### Required Software
- **Git**: [Download Git](https://git-scm.com/)
- **Python**: [Download Python](https://www.python.org/downloads/)
- **Docker** (optional, cho Milvus): [Download Docker](https://www.docker.com/)

## 🔧 Installation Steps

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd ai_agent_project
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your configuration
# Use your preferred text editor
notepad .env  # Windows
nano .env     # Linux/macOS
```

## 🗄️ Database Setup

### PostgreSQL Setup

#### Option 1: Local Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### Option 2: Docker
```bash
docker run --name postgres -e POSTGRES_PASSWORD=your_password -e POSTGRES_DB=your_database -p 5432:5432 -d postgres:15
```

#### Database Configuration
```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE your_database_name;

-- Create user
CREATE USER your_username WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;

-- Create sample tables (optional)
\c your_database_name

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES 
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com');
```

### Milvus Setup

#### Option 1: Docker (Recommended)
```bash
# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"

networks:
  default:
    name: milvus
EOF

# Start Milvus
docker-compose up -d

# Check status
docker-compose ps
```

#### Option 2: Local Installation
```bash
# Follow official guide: https://milvus.io/docs/install_standalone-docker.md
```

#### Test Milvus Connection
```python
from pymilvus import connections, utility

# Connect to Milvus
connections.connect("default", host="localhost", port="19530")

# List collections
collections = utility.list_collections()
print(f"Collections: {collections}")

# Create test collection (optional)
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

# Define schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128)
]
schema = CollectionSchema(fields, "test_collection")

# Create collection
collection = Collection("test_collection", schema)
print("Collection created successfully")
```

### Neo4j Setup

#### Option 1: Neo4j Desktop
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Install and create new project
3. Create database with password

#### Option 2: Docker
```bash
docker run --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your_password -d neo4j:5.0
```

#### Test Neo4j Connection
```python
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_password"))

# Test connection
with driver.session() as session:
    result = session.run("RETURN 1 as num")
    print(f"Connection test: {result.single()['num']}")

# Create test data (optional)
with driver.session() as session:
    session.run("CREATE (n:Person {name: 'John Doe', age: 30})")
    session.run("CREATE (n:Person {name: 'Jane Smith', age: 25})")
    print("Test data created")

driver.close()
```

## 🔑 API Configuration

### DeepSeek API
1. Visit [DeepSeek Console](https://platform.deepseek.com/)
2. Create account and get API key
3. Add to `.env`:
```env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL_ID=deepseek-chat
```

### OpenAI API
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create account and get API key
3. Add to `.env`:
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL_ID=gpt-4
```

### Anthropic API
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create account and get API key
3. Add to `.env`:
```env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL_ID=claude-3-sonnet-20240229
```

### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to `.env`:
```env
LLM_PROVIDER=gemini
LLM_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL_ID=gemini-pro
```

### Google Search API (Optional)
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Custom Search API
3. Create API key and Custom Search Engine
4. Add to `.env`:
```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
```

## 🧪 Testing Setup

### Test All Components
```bash
# Test LLM connection
python -c "from ai_agent.llm_client import get_llm_client; client = get_llm_client(); print('✅ LLM connected')"

# Test database connections
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='your_db', user='your_user', password='your_pass'); print('✅ PostgreSQL connected')"

# Test Milvus
python -c "from pymilvus import connections; connections.connect('default', host='localhost', port='19530'); print('✅ Milvus connected')"

# Test Neo4j
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password')); print('✅ Neo4j connected')"

# Test memory database
python -c "import sqlite3; conn = sqlite3.connect('memory.db'); print('✅ Memory DB accessible')"

# Test agent
python -c "from ai_agent.graph import build_graph; agent = build_graph(); print('✅ Agent loaded successfully')"
```

### Run Streamlit App
```bash
streamlit run streamlit_app.py
```

Access: http://localhost:8501

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

#### 2. Database Connection Issues
```bash
# Check if services are running
# PostgreSQL
sudo systemctl status postgresql

# Milvus (Docker)
docker-compose ps

# Neo4j
sudo systemctl status neo4j
```

#### 3. Memory Issues
```bash
# Clear memory database
rm memory.db

# Check memory usage
python -c "import sqlite3; conn = sqlite3.connect('memory.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM memory_entries'); print(f'Memory entries: {cursor.fetchone()[0]}')"
```

#### 4. LLM API Issues
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.deepseek.com/v1/models

# Check environment variables
python -c "import os; print('LLM_PROVIDER:', os.getenv('LLM_PROVIDER')); print('LLM_API_KEY:', os.getenv('LLM_API_KEY')[:10] + '...')"
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- PostgreSQL
CREATE INDEX idx_users_email ON users(email);
VACUUM ANALYZE;

-- Neo4j
CREATE INDEX FOR (n:Person) ON (n.name);
```

#### 2. Memory Management
```python
# Clear old memories
python -c "from ai_agent.memory import get_memory_manager; mm = get_memory_manager(); mm.clear_user_memory('old_user')"
```

#### 3. Connection Pooling
```python
# Use connection pooling for production
# Add to your database configuration
```

## 📊 Monitoring

### Log Files
```bash
# Check application logs
tail -f logs/app.log

# Check database logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Performance Metrics
```python
# Monitor memory usage
python -c "from ai_agent.memory import get_memory_manager; mm = get_memory_manager(); stats = mm.get_user_statistics('test_user'); print(stats)"
```

## 🔒 Security

### Production Checklist
- [ ] Use strong passwords for all databases
- [ ] Enable SSL/TLS for database connections
- [ ] Rotate API keys regularly
- [ ] Use environment-specific configurations
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

### Environment Variables Security
```bash
# Never commit .env files
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Milvus Documentation](https://milvus.io/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed information
4. Include logs and error messages

---

**Happy coding! 🚀**
