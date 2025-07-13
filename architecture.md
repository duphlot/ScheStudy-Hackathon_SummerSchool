# 🏗️ Kiến trúc hệ thống Summer School Hackathon

## Tổng quan
Hệ thống Summer School Hackathon là một AI Learning Assistant được thiết kế theo kiến trúc multi-agent với các thành phần được tách biệt rõ ràng, đảm bảo tính mở rộng và bảo trì.

## 🎯 Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                       │
│                      (Chainlit Web UI)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Chat Interface │  │  File Upload    │  │  Session Mgmt   │ │
│  │  (Real-time)    │  │  (Documents)    │  │  (Multi-user)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                      Agent Layer                                │
│                   (PydanticAI Framework)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Decision       │  │  Calendar       │  │  Knowledge      │ │
│  │  Agent          │  │  Agent          │  │  Search Agent   │ │
│  │  (Router)       │  │  (Scheduling)   │  │  (Q&A)          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Email Agent    │  │  Evaluation     │  │  Memory Handler │ │
│  │  (Reporting)    │  │  Agent          │  │  (Context)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Function Calls
┌─────────────────────────▼───────────────────────────────────────┐
│                      Tool System                                │
│                   (Extensible Tools)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Google         │  │  Search Tools   │  │  Communication  │ │
│  │  Calendar API   │  │  (Web, FAQ,     │  │  Tools (Email,  │ │
│  │                 │  │   Document)     │  │   Notifications)│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  File Processing│  │  Calculation    │  │  HTTP Tools     │ │
│  │  (PDF, XLSX)    │  │  (Math, Stats)  │  │  (REST APIs)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Data Access
┌─────────────────────────▼───────────────────────────────────────┐
│                       Data Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Milvus         │  │  Redis Cache    │  │  File System    │ │
│  │  Vector DB      │  │  (Session       │  │  (Documents,    │ │
│  │  (Embeddings,   │  │   Memory,       │  │   Configs,      │ │
│  │   Semantic      │  │   Chat History) │  │   Logs)         │ │
│  │   Search)       │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Google APIs    │  │  OpenAI APIs    │  │  External APIs  │ │
│  │  (Calendar,     │  │  (Embeddings)   │  │  (SMTP, Web     │ │
│  │   Drive)        │  │                 │  │   Search)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 Agent Architecture

### 1. Decision Agent (Router)
**Chức năng**: Phân loại yêu cầu của người dùng và định tuyến đến agent phù hợp.

```python
DECISION_PROMPT = """
Phân loại yêu cầu vào một trong hai loại:
1. "calendar" - quản lý lịch học, thời gian biểu
2. "web" - tìm kiếm kiến thức, câu hỏi học tập
"""
```

**Input**: User message  
**Output**: "calendar" hoặc "web"  
**Tools**: Không có tools, chỉ classification logic

### 2. Calendar Agent
**Chức năng**: Quản lý lịch học, tạo sự kiện, đọc lịch trình.

**Tools**:
- `create_calendar_event_simple`: Tạo sự kiện Google Calendar
- `read_calendar_events`: Đọc lịch trình hiện tại
- `safe_agent_run`: Thực hiện safe operations

**Workflow**:
```
User Request → Parse student info → Generate schedule → Create events → Confirm
```

### 3. Knowledge Search Agent
**Chức năng**: Tìm kiếm thông tin học tập từ web và tài liệu.

**Tools**:
- `search_web`: Tìm kiếm web
- `faq_tool`: Tìm trong FAQ database
- `search_relevant_document_tool`: Tìm tài liệu liên quan

### 4. Email Agent
**Chức năng**: Gửi báo cáo và thông báo tự động.

**Tools**:
- `send_email_tool`: Gửi email SMTP
- `get_latest_test_tool_func`: Lấy kết quả học tập

### 5. Evaluation Agent
**Chức năng**: Đánh giá và tạo báo cáo tiến độ học tập.

## 🔧 Component Details

### Presentation Layer (Chainlit)
```python
@cl.on_chat_start
async def start():
    # Initialize session
    
@cl.on_message 
async def main(message):
    # Route to appropriate agent
    decision = await agent_decision.run(message.content)
    
    if decision == "calendar":
        response = await agent_calendar.run(message.content)
    elif decision == "web":
        response = await agent_knowledge.run(message.content)
```

**Tính năng**:
- Real-time chat interface
- File upload support
- Session management
- Multi-user support
- Custom styling

### Agent Layer (PydanticAI)
```python
class AgentClient:
    def __init__(self, system_prompt: str, tools: List[Callable], model: GeminiModel):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
    
    def create_agent(self):
        return Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools
        )
```

**Đặc điểm**:
- Type-safe với Pydantic
- Async execution
- Tool integration
- Error handling
- Memory context

### Tool System
**Base Tool Structure**:
```python
def tool_function(input_data: InputModel) -> OutputModel:
    """Tool implementation"""
    # Process input
    # Call external APIs
    # Return structured output
```

**Tool Categories**:
1. **Calendar Tools**: Google Calendar API integration
2. **Search Tools**: Web search, document search, FAQ
3. **Communication Tools**: Email, notifications
4. **File Tools**: Reading, processing, merging files
5. **Utility Tools**: Calculator, HTTP requests

### Data Layer

#### Milvus Vector Database
```python
class MilvusClient:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._ensure_collection_exists()
    
    def search(self, query_vector: List[float], top_k: int = 5):
        # Hybrid search: semantic + BM25
        return results
```

**Schema**:
- `ID`: Primary key (auto-generated)
- `text`: Original text content
- `vector`: Dense embeddings (1536 dimensions)
- `sparse_vector`: Sparse BM25 vectors
- `metadata`: Additional fields (source, timestamp, etc.)

#### Redis Cache
```python
class ShortTermMemory:
    def __init__(self, max_messages: int = 15):
        self.max_messages = max_messages
    
    def store_message(self, session_id: str, message: str):
        # Store with TTL
    
    def get_history(self, session_id: str) -> List[str]:
        # Retrieve recent messages
```

**Caching Strategy**:
- Session-based memory (15 messages max)
- TTL-based expiration
- Message compression
- Context window management

## 🔄 Data Flow

### 1. User Request Flow
```
User Input → Chainlit UI → Decision Agent → Specific Agent → Tools → Response
```

### 2. Calendar Flow
```
Student ID + Subjects → Parse Info → Generate Schedule → Google Calendar API → Confirmation
```

### 3. Knowledge Search Flow
```
Question → Semantic Search (Milvus) → Web Search (fallback) → Response Generation
```

### 4. Memory Flow
```
Message → Redis Storage → Context Building → Agent Processing → Response Storage
```

## 🛡️ Security & Performance

### Security Measures
- **API Key Management**: Environment variables
- **Input Validation**: Pydantic models
- **Rate Limiting**: Per-session limits
- **Error Handling**: Comprehensive error catching
- **Sanitization**: Input/output sanitization

### Performance Optimizations
- **Async Processing**: Non-blocking operations
- **Caching**: Redis for frequently accessed data
- **Connection Pooling**: Database connections
- **Vector Indexing**: Optimized search performance
- **Memory Management**: Bounded context windows

## 📊 Monitoring & Logging

### Logging Strategy
```python
# config/logging_config.yaml
loggers:
  agents: INFO
  tools: DEBUG
  errors: ERROR
  performance: INFO
```

### Metrics Collection
- Response times
- Agent usage patterns
- Error rates
- Memory usage
- Cache hit rates

## 🚀 Deployment Architecture

### Development
```
Local Machine → Chainlit Dev Server → Local Redis/Milvus
```

### Production (Recommended)
```
Load Balancer → Container Cluster → Managed Redis → Cloud Vector DB
```

**Container Structure**:
```dockerfile
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["chainlit", "run", "workflow/ScheStudy.py", "--host", "0.0.0.0"]
```

## 🔮 Extensibility

### Adding New Agents
1. Create agent prompt in `src/data/prompts/`
2. Define tools for the agent
3. Add agent creation in workflow
4. Update decision logic if needed

### Adding New Tools
1. Implement tool in `src/utils/basetools/`
2. Follow the tool template structure
3. Add to `__init__.py` exports
4. Register with appropriate agents

### Custom UI Components
1. Extend Chainlit components
2. Add custom CSS in `public/`
3. Implement custom handlers in `src/handlers/`

## 📈 Scalability Considerations

### Horizontal Scaling
- Stateless agent design
- External session storage (Redis)
- Load balancer compatibility

### Vertical Scaling
- Memory-efficient operations
- Streaming responses
- Lazy loading of resources

### Database Scaling
- Milvus cluster setup
- Redis cluster/sentinel
- Connection pooling

---

> **Tài liệu này mô tả kiến trúc chi tiết của hệ thống. Để biết thêm thông tin về implementation cụ thể, tham khảo source code và documentation trong thư mục `docs/`.**