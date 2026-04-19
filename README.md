# Big Data — 文档解析存储系统

Monorepo 项目，包含后端文档解析服务和前端管理界面。

## 项目结构

```
.
├── document-parser-backend/    # 后端：FastAPI + Celery + PostgreSQL + MinIO + PaddleOCR
│   ├── src/                    #   后端源码
│   ├── tests/                  #   测试代码
│   ├── docker-compose.yml      #   依赖服务（PostgreSQL/Redis/MinIO）
│   └── pyproject.toml          #   后端依赖
└── big-data-frontend/          # 前端：Vue 3 + Vite + TypeScript
    └── src/                    #   前端源码
```

## 功能特性

- 多格式文档解析：Word、Excel、PDF、图片、邮件、文本
- 异步任务处理：Celery + Redis 后台解析
- 文件存储：MinIO 对象存储
- 数据持久化：PostgreSQL 数据库
- 可插拔解析器架构，便于扩展

## 支持格式

| 格式 | 扩展名 | 解析器 |
|------|--------|--------|
| Word | .docx | DocxParser |
| Excel | .xlsx/.xls/.csv | ExcelParser |
| PDF | .pdf | PdfTextParser |
| 图片 | .png/.jpg/.jpeg/.bmp | OcrParser (PaddleOCR) |
| 邮件 | .eml | EmlParser |
| 邮件 | .msg | MsgParser |
| 文本 | .txt/.md/.json/.xml/.yaml | TextParser |

## 技术栈

- **后端**: FastAPI + Celery + Redis + PostgreSQL + MinIO
- **前端**: Vue 3 + Vite + TypeScript + Vue Router + Pinia + Axios
- **OCR**: PaddleOCR

## 快速开始

### 1. 启动依赖服务

```bash
cd document-parser-backend
docker-compose up -d
```

> 如果报错 "container name already in use"，先清理残旧容器：
> ```bash
> docker-compose down && docker-compose up -d
> ```

### 2. 安装后端依赖

```bash
conda activate bigData
pip install -e .
```

### 3. 安装前端依赖

```bash
cd ../big-data-frontend
npm install
```

### 4. 启动服务

> 所有后端命令需在 `conda activate bigData` 环境下执行。

#### 4.1 启动 FastAPI 后端（终端 1）

```bash
cd ../document-parser-backend
uvicorn src.app.main:app --reload --port 8000
```

> **端口被占用？**
> ```bash
> lsof -ti:8000       # 查看占用进程
> kill -9 <PID>       # 杀掉后重启，或换端口：--port 8001
> ```

#### 4.2 启动 Celery Worker（终端 2）

```bash
cd document-parser-backend
celery -A src.core.celery worker -l info --pool=solo
```

> **关键：** `[tasks]` 下方必须显示 `src.tasks.parser_task.parse_document`，否则任务不会执行。
> 如果之前启动过 worker，需要先清理旧进程：
> ```bash
> pkill -f "celery -A src.core.celery"
> ```

#### 4.3 启动前端（终端 3）

```bash
cd big-data-frontend
npm run dev
```

> 前端默认代理到 `http://localhost:8000`。如果后端用了其他端口，修改 `vite.config.ts` 的 `server.proxy.target`。

### 5. 验证

访问 http://localhost:5173 使用前端界面，或：

```bash
curl http://localhost:8000/health
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/files` | 上传文件 |
| GET | `/files` | 文档列表（支持 `page`, `page_size` 分页） |
| GET | `/files/{id}` | 查询文件状态和详情 |
| GET | `/files/{id}/content` | 获取解析后的文本内容 |
| PUT | `/files/{id}/content` | 保存编辑后的文本内容 |
| GET | `/health` | 健康检查 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | postgresql://docuser:docpass@localhost:5432/docparser | 数据库连接 |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接 |
| MINIO_ENDPOINT | localhost:9000 | MinIO 地址 |
| MINIO_ACCESS_KEY | minioadmin | MinIO AK |
| MINIO_SECRET_KEY | minioadmin | MinIO SK |
| MINIO_BUCKET | documents | 存储桶名称 |

## 测试

```bash
cd document-parser-backend
pytest tests/ -v
```

## 许可证

MIT License
