# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

Monorepo 结构，包含后端和前端两个子项目：

- `document-parser-backend/` — 文档解析存储系统后端（FastAPI + Celery/Redis + PostgreSQL + MinIO + PaddleOCR）
- `big-data-frontend/` — 前端管理界面（Vue 3 + Vite + TypeScript）

项目详细说明参见 `README.md`。

---

## 子项目配置

### 后端（document-parser-backend/）

后端项目有独立的 `CLAUDE.md`，位于 `document-parser-backend/claude.md`，包含后端架构、解析器架构等详细技术文档。

工作目录切换到 `document-parser-backend/` 时，会自动加载该目录下的 `.claude/settings.local.json` 和 `claude.md`。
