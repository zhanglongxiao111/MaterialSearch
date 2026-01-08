# MaterialSearch

**AI-Powered Local Asset Search Engine** | Search your design library with natural language or images

---

## ✨ Features

- 🔍 **Text-to-Image/Video** - Find assets using natural language descriptions
- 🖼️ **Image-to-Image/Video** - Upload an image to find similar content
- 📁 **Multi-Library** - Separate permanent and project-based storage
- 📄 **PDF Indexing** - Auto-render and index PDF pages
- 🚀 **Batch Import** - Drag & drop folders to build your library
- 🖥️ **Desktop App** - Cross-platform Tauri client

---

## 🎯 Project Vision

Building an **AI Workstation** for architectural design firms:

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 1** | Asset Search Engine | ✅ Complete |
| **Phase 2** | RAG Knowledge Base | 🔜 Planned |
| **Phase 3** | AI Image Generation | 🔜 Planned |
| **Phase 4** | Agent Workflow Automation | 🔜 Planned |

---

## 🚀 Quick Start

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure asset path (edit .env)
ASSETS_PATH=/path/to/your/assets

# Start server
python main.py
```

Visit http://localhost:58888

### Docker Deployment

```bash
docker-compose up -d
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + Flask + SQLAlchemy |
| AI Model | Chinese-CLIP (HuggingFace) |
| Vector Search | FAISS / pgvector |
| Frontend | Vue.js + Vanilla CSS |
| Desktop | Tauri (Rust) |
| Deployment | Docker + Supabase (optional) |

---

## 📖 Documentation

- [Project Docs](openspec/project.md)
- [Changelog](CHANGELOG_PROJECT.md)
- [Development Guide](docs/MIGRATION_SPEC.md)

---

## 📄 License

Forked from [MaterialSearch](https://github.com/chn-lee-yumi/MaterialSearch)  
GNU GPLv3 License
