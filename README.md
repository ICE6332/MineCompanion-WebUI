# MineCompanionAI-WebUI

> **仓库已归档**
> **为 Minecraft AI 伴侣模组提供的智能控制面板**
> v0.5.0-beta | [GitHub 仓库](https://github.com/ICE6332/MineCompanion-BOT)

一个现代化的 Web 应用，帮助你配置和管理 Minecraft 中的 AI 伴侣。通过直观的界面轻松设置 AI 人格、测试对话效果、监控运行状态。

---

## 🌟 主要功能

- 🤖 **AI 对话测试**: 在游戏外测试 AI 伴侣的对话效果，支持重新生成回复
- 🧪 **WebSocket 测试**: 发送自定义 JSON 消息，测试 Mod ↔ Service 通信链路
- 📊 **监控面板**: 实时查看系统运行状态、消息统计和 Token 使用趋势
- ⚙️ **模型设置**: 支持多种 LLM 提供商（OpenAI、Claude、Gemini 等）
- 🌐 **Web 界面**: 友好的中文界面，响应式设计，支持暗色模式
- 🚀 **一键启动**: 自动打开浏览器，显示启动信息，无需手动配置

---

## 📋 系统要求

在开始之前，请确保你的系统已安装：

- **Node.js** >= 18.0.0 ([下载地址](https://nodejs.org/))
- **Python** >= 3.14 ([下载地址](https://www.python.org/downloads/))
- **uv** (Python 包管理器，十分推荐) ([安装指南](https://github.com/astral-sh/uv))

### 安装 uv（推荐）

**Windows (PowerShell)**:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**Linux/macOS**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🚀 快速开始

### 0. 获取项目

**方式一：从 Release 下载（推荐普通用户）**

1. 访问 [Releases 页面](https://github.com/ICE6332/MineCompanion-WebUI/releases)
2. 下载最新版本的 `Source code (zip)` 或 `Source code (tar.gz)`
3. 解压到任意目录

**方式二：使用 Git Clone（推荐开发者）**

```bash
git clone https://github.com/ICE6332/MineCompanion-WebUI.git
cd MineCompanion-WebUI
```

### 1. 安装依赖

**首次安装时，依次运行以下命令**：

```bash
# 安装 Python 依赖
uv sync

# 安装根目录 Node.js 依赖
npm install
```

> 💡 `uv sync` 会自动创建 Python 虚拟环境并安装所有后端依赖

### 2. 启动应用

**一键启动（推荐）**：
```bash
npm start
```

启动成功后，浏览器会自动打开 http://localhost:8080，你将看到：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 MineCompanionAI-WebUI 已成功启动！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Web 界面:  http://localhost:8080
📖 API 文档:  http://localhost:8080/docs
🔧 健康检查:  http://localhost:8080/health
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 提示: 按 Ctrl+C 停止服务器
```

---

## 📖 使用指南

### 配置 LLM 提供商

首次使用前，需要配置大语言模型（LLM）：

1. 访问 http://localhost:8080
2. 进入 **"模型设置"** 页面（左侧菜单）
3. 选择你的 LLM 提供商：
   - **OpenAI**: 需要 API Key（[获取地址](https://platform.openai.com/api-keys)）
   - **自定义 API**: 支持任何 OpenAI 兼容的 API（如 Ollama、LiteLLM）
4. 填写配置信息：
   - Provider（提供商）: 如 `openai`
   - Model（模型名称）: 如 `gpt-4o`, `gpt-3.5-turbo`
   - API Key（密钥）: 你的 API 密钥
   - Base URL（可选）: 自定义 API 端点
5. 点击 **"保存配置"**

> ⚠️ 配置保存后会自动应用，无需重启服务

### 测试 AI 对话

配置完成后，进入 **"AI 对话测试"** 页面：

1. 在输入框中输入消息
2. 选择要使用的模型（右下角下拉菜单）
3. 点击发送按钮（或按 Enter）
4. AI 回复后，你可以：
   - 📋 **复制回复内容**（点击复制按钮）
   - 🔄 **重新生成回复**（点击刷新按钮）
   - 👍👎 **反馈评价**（点赞/点踩）

> 💡 每次对话都会生成新的回复，不会使用缓存

### 测试 WebSocket 通信

**角色测试** 页面实际上是一个 **WebSocket 测试工具**，用于验证 Mod ↔ Service 通信链路：

1. 进入 **"角色测试"** 页面
2. 在编辑器中修改 JSON 消息内容
3. 示例消息格式：
   ```json
   {
     "type": "conversation_message",
     "data": {
       "companionName": "AICompanion",
       "text": "你好，这是测试消息"
     }
   }
   ```
4. 点击 **"发送 JSON 消息到模组"** 按钮
5. 在 Minecraft 游戏内的聊天栏查看效果

> 💡 此功能主要用于开发调试，确保前端能正确与游戏模组通信

### 监控系统状态

**监控面板** 显示实时运行数据：

- **连接状态**: Mod 连接、LLM 提供商
- **消息统计**: 收发消息数量、类型分布
- **Token 趋势**: 24 小时 Token 使用量图表
- **事件日志**: 实时事件流（WebSocket 消息、LLM 请求等）

---

## 🎨 界面预览

### 控制台
- 查看系统概览、统计数据和图表

### AI 对话测试
- 测试 AI 伴侣的对话效果，调整模型参数

### 角色测试 (WebSocket 工具)
- 发送自定义 JSON 消息，测试 Mod 通信

### 监控面板
- 实时监控系统运行状态和事件

### 模型设置
- 配置 LLM 提供商和 API 密钥

---

## 🔧 高级配置

### 环境变量

你可以通过 `.env` 文件自定义配置：

```bash
# 存储后端（memory 或 redis）
STORAGE_BACKEND=memory

# Redis 配置（使用 redis 时）
REDIS_URL=redis://localhost:6379

# LLM 缓存
LLM_CACHE_ENABLED=true
LLM_CACHE_TTL=3600

# 监控配置
EVENT_HISTORY_SIZE=100
RATE_LIMIT_MESSAGES=100
RATE_LIMIT_WINDOW=60
```

### 生产部署

如果你想在生产环境运行：

```bash
# 1. 编译前端
cd frontend && npm run build

# 2. 启动后端（生产模式）
npm start
```

> 生产模式下，后端会自动提供编译后的前端静态文件

---

## 🐛 常见问题

### Q: 启动时提示 "uv: command not found"
**A**: 请按照上方说明安装 uv，或使用 pip 安装依赖：
```bash
pip install -r requirements.lock.txt
```

### Q: 浏览器没有自动打开
**A**: 手动访问 http://localhost:8080 即可

### Q: LLM 请求失败，提示 "API Key 未配置"
**A**: 请先进入"模型设置"页面配置 LLM 提供商和 API Key

### Q: 前端显示"无法连接到后端"
**A**: 检查后端是否正常启动：
```bash
curl http://localhost:8080/health
```
如果返回 `{"status":"ok"}` 说明后端正常

### Q: Windows 控制台显示乱码
**A**: 这是 Windows GBK 编码问题，不影响功能，可以忽略

### Q: 如何更换 LLM 模型？
**A**: 在"AI 对话测试"页面右下角的下拉菜单中选择，或者在"模型设置"中修改默认模型

---

## 📦 项目结构

```
MineCompanionAI-WebUI/
├── api/              # FastAPI 后端路由
├── core/             # 核心业务逻辑（LLM、存储、监控）
├── config/           # 配置文件和角色卡存储
├── models/           # 数据模型（Pydantic）
├── static/dist/      # 网页文件
├── scripts/          # 启动脚本
├── main.py           # 后端入口
└── README.md         # 本文档
```

> 📝 前端源码在开发分支 `develop/0.5.0-beta` 中

---

## 🗺️ 版本说明

### v0.5.0-beta (当前版本)

**新增功能**:
- ✅ AI 对话测试页面（支持重新生成）
- ✅ WebSocket 测试工具（发送自定义 JSON 消息）
- ✅ 实时监控面板（WebSocket 事件流）
- ✅ Token 使用趋势图表（24 小时）
- ✅ 多 LLM 提供商支持（OpenAI、Claude、Gemini 等）
- ✅ 启动横幅和自动浏览器打开
- ✅ 生产模式静态文件服务

**已知问题**:
- Windows 控制台可能显示编码错误（不影响功能）
- 角色卡管理功能尚未实现（计划中）
- AI 对话测试无法保存
- 分析页面目前为UI展示，尚未实现功能

**下个版本计划**:
- 角色卡 CRUD 功能（创建、编辑、删除角色）
- 会话历史管理
- 记忆系统（短期/长期记忆）
- 决策引擎集成
- UI 逻辑实现
- 实现游戏内交互功能

---

## 💬 反馈与支持

- **问题反馈**: [GitHub Issues](https://github.com/ICE6332/MineCompanion-BOT/issues)
- **功能建议**: 在 Issues 中提出你的想法
- **文档贡献**: 欢迎 PR 改进文档

---

## 📄 开源协议

本项目采用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 协议开源。

**允许的商业行为**：
- ✅ 在企业内部部署和使用（无需公开源码）
- ✅ 为客户定制开发并交付源码（需遵守 AGPL-3.0）
- ✅ 基于本项目提供技术支持和咨询服务

**禁止的商业行为**：
- ❌ 闭源商业化（将修改后的代码作为专有软件销售）
- ❌ SaaS 闭源运营（提供在线服务但不公开修改后的源码）
- ❌ 集成到闭源产品中（除非整个产品也采用 AGPL-3.0）

### 免责声明

本软件按"原样"提供，不提供任何明示或暗示的担保，包括但不限于适销性、特定用途的适用性和非侵权性的担保。在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责，无论是在合同诉讼、侵权行为还是其他方面。

---

**享受你的 AI 伙伴吧！** 🎮✨

---

**注意**：使用本项目前，请仔细阅读并理解 AGPL-3.0 协议条款。如有疑问，建议咨询法律顾问。
