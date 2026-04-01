# Summer School Hackathon - AI Learning Assistant

Một hệ thống trợ lý học tập thông minh sử dụng AI để hỗ trợ sinh viên trong việc quản lý lịch học, tìm kiếm kiến thức và gửi báo cáo tự động.

## Tính năng chính

### AI Agent Platform
- **Multi-Agent System**: Hệ thống đa agent chuyên biệt cho từng loại nhiệm vụ
- **PydanticAI Integration**: Framework hiện đại cho AI agents với type safety
- **Google Gemini 2.0**: LLM mạnh mẽ với context window lớn và khả năng reasoning cao
- **Decision Making**: Agent phân loại tự động yêu cầu người dùng

### Calendar Management
- **Google Calendar Integration**: Tự động tạo và quản lý lịch học
- **Smart Scheduling**: Lập kế hoạch ôn tập cá nhân hóa dựa trên mã sinh viên và tổ hợp môn
- **Event Creation**: Tạo sự kiện học tập với thông tin chi tiết

### Knowledge Search & FAQ
- **Vector Database**: Milvus vector DB cho semantic search
- **Hybrid Search**: Kết hợp semantic search và keyword search (BM25)
- **Document Processing**: Xử lý và index tài liệu học tập
- **Web Search Integration**: Tìm kiếm thông tin từ web khi cần

### Conversational UI
- **Chainlit Interface**: Giao diện chat hiện đại và thân thiện
- **Session Management**: Quản lý phiên chat đa người dùng
- **Memory System**: Lưu trữ ngắn hạn với Redis
- **Real-time Updates**: Cập nhật conversation theo thời gian thực

### 📧 Automated Reporting
- **Email Integration**: Gửi báo cáo tự động qua email
- **Weekly Reports**: Báo cáo cuối tuần về tình hình học tập
- **Student Progress**: Theo dõi và báo cáo tiến độ học tập

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│                     (Chainlit Web UI)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Agent Orchestration                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Decision       │  │  Calendar       │  │  Knowledge      │ │
│  │  Agent          │  │  Agent          │  │  Agent          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     Tool System                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Google         │  │  Search Tools   │  │  Email Tools    │ │
│  │  Calendar       │  │  (Web, FAQ)     │  │  (SMTP)         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Milvus         │  │  Redis Cache    │  │  File System    │ │
│  │  (Vector DB)    │  │  (Memory)       │  │  (Documents)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Cài đặt và sử dụng

### 1. Yêu cầu hệ thống
- Python 3.12+
- Redis Server
- Milvus Vector Database
- Google API credentials

### 2. Cài đặt dependencies
```bash
# Clone repository
git clone https://github.com/duphlot/summerschool_hackathon.git
cd summerschool_hackathon

# Cài đặt packages
pip install .
```

### 3. Cấu hình môi trường
Tạo file `.env` với các biến môi trường:
```env
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key

# Vector Database
MILVUS_URI=your_milvus_uri
MILVUS_TOKEN=your_milvus_token

# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password

# Google Calendar API
GOOGLE_CALENDAR_CREDENTIALS=path_to_credentials.json

# Redis (nếu không dùng default)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Chạy ứng dụng
```bash
# Chạy main application
chainlit run workflow/ScheStudy.py
```

## 📁 Cấu trúc dự án

```
summerschool_hackathon/
├── src/
│   ├── data/
│   │   ├── cache/           # Redis memory management
│   │   ├── embeddings/      # Text embedding utilities
│   │   ├── milvus/          # Vector database client
│   │   ├── prompts/         # AI prompts cho các agents
│   │   └── mock_data/       # Dữ liệu test và demo
│   ├── handlers/            # UI và error handlers
│   ├── llm/                 # LLM wrappers và agents
│   ├── utils/               # Utilities và tools
│   │   └── basetools/       # Custom tools (calendar, email, search)
│   └── prompt_engineering/  # Prompt optimization
├── workflow/                # Main applications
├── config/                  # Configuration files
├── docs/                    # Documentation
└── public/                  # Static assets
```

## Các Tools có sẵn

### Calendar Tools
- `create_calendar_event_simple`: Tạo sự kiện Google Calendar
- `read_calendar_events`: Đọc lịch trình hiện tại
- `safe_agent_run`: Safe execution cho calendar operations

### Search Tools
- `search_web`: Tìm kiếm thông tin trên web
- `faq_tool`: Tìm kiếm trong FAQ database
- `search_in_file_tool`: Tìm kiếm trong file cụ thể
- `search_relevant_document_tool`: Tìm tài liệu liên quan

### Communication Tools
- `send_email_tool`: Gửi email tự động
- `get_latest_test_tool_func`: Lấy thông tin kết quả học tập

### Utility Tools
- `calculator_tool`: Máy tính cơ bản và nâng cao
- `file_reading_tool`: Đọc và xử lý file
- `http_tool`: HTTP requests
- `merge_files_tool`: Hợp nhất files

## 💡 Ví dụ sử dụng

### Tạo lịch học
```
"Mã số sinh viên của tôi là 20250001, tôi muốn thi tổ hợp toán, lý, hóa"
```

### Tìm kiếm kiến thức
```
"Giải thích về machine learning cho người mới bắt đầu"
```

### Báo cáo tiến độ
```
"Gửi báo cáo kết quả học tập tuần này"
```

## Customization

### Thêm Agent mới
```python
from llm.base import AgentClient

custom_agent = AgentClient(
    model=model,
    system_prompt="Your custom prompt",
    tools=[your_custom_tools]
).create_agent()
```

### Thêm Tool mới
```python
def custom_tool(input_data: str) -> str:
    """Your custom tool implementation"""
    return processed_result
```

### Custom UI
```python
@cl.on_chat_start
async def start():
    await cl.Message(content="Custom welcome message").send()
```

## Performance & Monitoring

- **Memory Management**: Redis-based short-term memory với configurable retention
- **Vector Search**: Milvus với hybrid search optimization
- **Error Handling**: Comprehensive error handling and logging
- **Session Management**: Multi-user session support

## Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

## 📄 License

Dự án này dành cho mục đích giáo dục và thử nghiệm.

## Team

Phát triển trong khuôn khổ Summer School Hackathon.

---

> **Lưu ý**: Đây là một dự án demo cho hackathon. Để sử dụng trong production, cần bổ sung thêm security, monitoring và optimization.
