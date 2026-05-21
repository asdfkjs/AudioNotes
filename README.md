# AudioNotes - 基于 FunASR 的音频转结构化笔记系统

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FunASR](https://img.shields.io/badge/ASR-FunASR-orange.svg)](https://github.com/modelscope/FunASR)
[![LLM](https://img.shields.io/badge/LLM-Qwen3--8B-green.svg)](https://github.com/QwenLM/Qwen)

本项目为计算机科学与技术专业本科毕业设计。AudioNotes 是一个基于端到端语音识别技术与大型语言模型的音视频结构化笔记系统，旨在解决长音频（如会议记录、课堂笔记）转写后缺乏语义组织、可读性差的问题，实现了从“听得清”到“听得懂”的自动化知识整理闭环。

## ✨ 核心功能

- **🎙️ 高精度语音转写**：内置阿里达摩院 FunASR 引擎（支持 fallback 至 faster-whisper），结合 VAD 语音活动检测，精准切分长音频，提升复杂场景识别率。
- **📝 智能结构化笔记**：通过本地部署的 Qwen3-8B 大语言模型，自动对冗长的语音转写文本进行语义归纳，生成包含“概述、要点、待办、结论”的格式化 Markdown 笔记。
- **💬 多轮会话式交互**：支持基于生成的笔记内容进行多轮追问与检索，严格约束上下文，减少大模型幻觉。
- **🔐 多用户认证门户**：独立的 Flask 用户管理门户，支持注册与密码修改，保障个人笔记数据的隐私性。
- **💾 结构化数据沉淀**：依托 PostgreSQL 实现会话、消息、原文件与笔记的高效持久化管理，历史数据可随时追溯。

## 🛠️ 技术栈

- **前端交互**：[Chainlit](https://docs.chainlit.io/) (流式对话与 Web 界面)
- **后端服务**：Python 3.10, Flask (用户门户)
- **核心算法**：FunASR (语音识别), Ollama + Qwen3-8B (文本理解与生成)
- **数据存储**：PostgreSQL, SQLAlchemy

## 📂 项目结构

```text
audio-notes-main/
├── app/                    # 核心业务逻辑代码
│   ├── services/           # 模型服务层 (FunASR, Ollama API, 数据层)
│   └── utils/              # 通用工具类 (路径处理, UUID生成等)
├── docs/                   # 项目文档与答辩资料
├── storage/                # 本地存储目录 (录音、临时文件、SQLite 等)
├── main.py                 # Chainlit 主程序入口 (笔记与对话系统)
├── portal.py               # Flask 用户管理系统入口
├── requirements.txt        # Python 依赖清单
├── docker-compose.yml      # Docker 容器编排文件 (数据库等基础设施)
├── Dockerfile              # 应用镜像构建脚本
├── .env.example            # 环境变量配置模板
└── users.json              # 独立门户用户鉴权数据
```

## 🚀 快速开始

### 1. 环境准备

确保您的设备已安装以下环境：
- Python >= 3.10
- FFmpeg >= 4.4 (用于音频格式标准化与重采样)
- Ollama >= 0.1.20 (用于本地运行大语言模型)
- Docker & Docker Compose (可选，用于快速部署数据库)

### 2. 克隆与安装依赖

```bash
git clone [https://github.com/your-username/AudioNotes.git](https://github.com/your-username/AudioNotes.git)
cd AudioNotes

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Windows 下使用 .venv\Scripts\activate

# 安装项目依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境模板文件并根据需要进行修改：

```bash
cp .env.example .env
```
请在 `.env` 中正确配置数据库连接参数以及 Ollama API 地址。

### 4. 启动底层服务 (数据库 & 模型)

```bash
# 1. 启动 PostgreSQL 数据库容器
docker-compose up -d

# 2. 在本地 Ollama 中拉取/运行 Qwen3-8B 模型
ollama run qwen3:8b
```

### 5. 启动系统

项目由两部分构成，建议在两个独立的终端窗口中启动：

**终端 A：启动用户管理门户 (Flask)**
```bash
python portal.py
# 访问 http://localhost:5000 进行用户注册或密码修改
```

**终端 B：启动主笔记系统 (Chainlit)**
```bash
chainlit run main.py -w
# 系统会自动打开浏览器并访问 http://localhost:8000
```

## 📦 数据集与微调模型下载

为了保证 GitHub 仓库的轻量化，项目所用的庞大数据集和基于 LoRA 训练的大模型权重文件已存放在云盘。

- **微调模型 (Qwen3-8B-Q4_K_M_lora.gguf)**: [点击这里下载 ()]
- **自建语音评测数据集**: [点击这里下载 ()]

*(注：模型文件配置请参考仓库根目录下的 `Modelfile` 和 `train_info.md` 了解微调细节。下载模型权重后，请将其导入 Ollama 中使用，具体方法参见 `train_info.md`。)*

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。
