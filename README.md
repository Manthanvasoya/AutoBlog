# AutoBlog — Autonomous Multi-Agent Blog Generation & Publishing System

A fully autonomous blog generation pipeline powered by LangGraph, where a user provides a topic and the system automatically plans, researches, writes, visualizes, and publishes content to Dev.to and Medium.

## 🏗️ Architecture

**11-Node LangGraph Pipeline:**

```
START
  ↓
1. Planner agent (HITL 1) — plans structure, decides if research needed
  ↓
2. Research agent (conditional) — Tavily API search
  ↓
3. Outline agent (HITL 2) — generates blog structure with pre-filtered facts
  ↓
4. Writer agent (Send API fan-out) — parallel section writing
  ↓
5+6. Visual + SEO agents (parallel) — charts, cover image, metadata
  ↓
7. Assembler node (pure Python) — embeds visuals + SEO frontmatter
  ↓
8. Critic agent (HITL 3) — quality evaluation with retry loop
  ↓
9. Publisher agent — Dev.to → Medium (with canonical URL)
  ↓
END — Live on Dev.to + Medium
```

## 🛠️ Tech Stack

- **LangGraph** — Agent orchestration & state management
- **LangChain** — LLM abstractions
- **OpenAI / Anthropic** — LLM providers
- **Tavily** — Internet research API
- **SQLite** — LangGraph checkpointing (HITL pause/resume)
- **MongoDB** — Application data (blogs, SEO, quality logs)
- **Streamlit** — Frontend UI with 3 interactive checkpoints & Published Blog History
- **Matplotlib** — Chart generation
- **Pollinations.ai** — Free, on-the-fly cover image generation (Replaced DALL-E)

## 📦 Installation

### 1. Clone / Setup

```bash
cd OneBlog
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` with your API keys:

```bash
cp .env.example .env
# Edit .env with:
# - OPENAI_API_KEY
# - TAVILY_API_KEY
# - DEVTO_API_KEY
# - MEDIUM_ACCESS_TOKEN
# - MONGODB_URI
```

### 3. Database Setup

**SQLite** — automatically created at `data/blog_checkpoints.db`

**MongoDB** — ensure local MongoDB running or update `MONGODB_URI` in `.env`:

```bash
# Local MongoDB
mongod

# Or use MongoDB Atlas cloud
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

## 🚀 Running the System

### Start the Streamlit app:

```bash
python scripts/run.py
# Or directly:
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`

## 📋 Project Structure

```
OneBlog/
├── src/
│   ├── core/          # State definitions, config, constants
│   ├── database/      # MongoDB + SQLite operations
│   ├── llm/           # LLM models + prompts for all agents
│   ├── agents/        # 8 LLM-powered agents (Planner through Publisher)
│   ├── nodes/         # Pure Python nodes (Assembler)
│   ├── graph/         # LangGraph workflow definition
│   ├── tools/         # API wrappers (Tavily, Dev.to, Medium)
│   └── utils/         # Logging, validation, helpers
│
├── frontend/          # Streamlit UI with 3 HITL checkpoints
│   ├── app.py
│   └── pages/         # Individual checkpoint pages
│
├── tests/             # Unit & integration tests
│
├── scripts/
│   ├── run.py         # Streamlit entry point
│   └── test_pipeline.py
│
└── config.yaml        # LLM settings, timeouts, etc.
```

## 🎯 How It Works

### 1. **Planner** (HITL 1)
- Analyzes topic
- Decides if internet research needed (needs_research flag)
- Generates outline hints, visual requirements
- **User approves or provides feedback**

### 2. **Research** (Conditional)
- Only runs if `needs_research == True`
- Searches Tavily for key facts
- Extracts facts (never full articles — token optimization)

### 3. **Outline** (HITL 2)
- Generates blog structure with 3-7 sections
- Sets max_words per section (Python hard caps at 300)
- Pre-filters research facts per section
- **User reviews structure and estimated word counts**

### 4. **Writer** (Dynamic Parallel)
- Writes each section independently via Send API
- Parallel execution: 6 sections written simultaneously
- Incorporates pre-filtered facts naturally
- Context-pruned per agent: ~1500 tokens per section (vs ~8000 full state)

### 5. **Visual + SEO** (Parallel Batch)
- **Visual agent:** Generates Matplotlib charts + Pollinations.ai cover image URLs directly
- **SEO agent:** Tags, slug, meta_description, keywords
- Both run simultaneously (no dependencies)
- Results merged before assembly

### 6. **Assembler** (Pure Python)
- Combines: SEO frontmatter + draft + embedded charts
- Creates final publishable markdown
- **Why pure Python:** Deterministic formatting, no LLM overhead

### 7. **Critic** (HITL 3, Retry Loop)
- Evaluates assembled blog on:
  - **Depth (40%):** Thorough coverage?
  - **Clarity (30%):** Clear writing?
  - **Grounding (30%):** Facts backed by research?
- Composite score: `(0.4 × depth) + (0.3 × clarity) + (0.3 × grounding)`
- If score < 0.75 AND iterations < 3: loops back to Writer
- **User approves or provides new feedback**

### 8. **Publisher**
- Publishes to **Dev.to first** (synchronous, gets URL immediately)
- Publishes to **Medium second** with `canonicalUrl` = Dev.to URL
- Sets `published: True`, stores in MongoDB

## 💡 Key Design Decisions

### Why Conditional Research?
Planner sets `needs_research` upfront. Evergreen topics skip Tavily entirely (cost + latency savings).

### Why Send API for Section Writing?
Each section is independent. Writing 6 sections in parallel is 6x faster than sequential.

### Why Context Pruning per Agent?
Each agent receives only relevant fields (~60% token reduction). Writer gets 1500 tokens instead of 8000.

### Why Assembler Node?
Writer produces raw markdown. Visual and SEO produce assets separately. Assembler combines them deterministically. **Critic evaluates the actual publishable blog**, not raw text.

### Why SQLite + MongoDB?
- **SQLite:** Exclusive use for LangGraph checkpointing. Zero manual schema management.
- **MongoDB:** Application data (blogs, SEO, quality logs). Schema-free model fits variable content perfectly. The system stores the **full markdown text** of every generated blog directly in MongoDB for historical reference.

### Why Dev.to Before Medium?
Dev.to publishes synchronously and returns live URL immediately. Medium needs this URL as canonical source to prevent Google duplicate content penalty.

## 🧪 Testing

Run integration tests:

```bash
python tests/integration/test_workflow.py
```

Expected output:
```
✓ Workflow created successfully
✓ Graph has 11 nodes
✓ Initial state created successfully
✅ All tests passed!
```

## 📊 Monitoring & Debugging

**View execution trace:**
- Streamlit sidebar shows which node is currently running
- SQLite checkpoints store full state at each HITL pause

**View quality logs:**
- MongoDB `blog_quality_log` collection stores every critic evaluation
- Track scores and feedback across iterations

**View published blogs:**
- **Streamlit Sidebar:** The UI automatically queries MongoDB to list your last 15 published blogs. Clicking them opens a dedicated "Metadata View" rendering the full markdown content, statistics, and live Dev.to/Medium links.
- MongoDB `blogs` collection stores final records.

## 🔧 Configuration

Edit `config.yaml` for:
- LLM model selection & temperature
- Max tokens per agent
- API timeouts
- Blog constraints (min/max sections, word counts)
- Publishing settings

## 📝 Example Usage

1. **Start app:**
   ```bash
   streamlit run frontend/app.py
   ```

2. **Enter topic:** "How Large Language Models Work"

3. **HITL 1 (Planner):** Review plan, approve structure

4. **HITL 2 (Outline):** Review outline with estimated word counts

5. **Parallel writing & visualization** (automatic)

6. **HITL 3 (Critic):** Review quality scores, approve for publishing

7. **Automatic publishing** → Live on Dev.to + Medium

## 🚀 Deployment

### Local:
```bash
streamlit run frontend/app.py
```

### Cloud (Streamlit Cloud):
```bash
streamlit run frontend/app.py --logger.level=info
```

### Docker:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py"]
```

## 📈 Performance

- **Planner:** ~3 seconds
- **Research:** ~10 seconds (if needed)
- **Outline:** ~4 seconds
- **Writer (6 sections parallel):** ~15 seconds
- **Visual + SEO (parallel):** ~8 seconds
- **Assembler:** <1 second
- **Critic:** ~3 seconds
- **Publisher:** ~5 seconds

**Total pipeline:** ~50 seconds end-to-end (with research)

## 🐛 Troubleshooting

### `LangGraphError: Node not found`
Ensure all agents are imported in `src/graph/workflow.py`

### `MongoDBServerSelectionTimeoutError`
Verify MongoDB URI in `.env` and ensure MongoDB is running

### `StreamHandler missing API key`
Check `.env` file has `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`.

### `Dev.to API Error 422: Unprocessable Entity`
- Ensure tags are strictly alphanumeric with no spaces, and limited to a maximum of 4 tags.
- Ensure the `cover_image` is a valid public HTTP URL (which is handled automatically by Pollinations.ai) rather than a local file path.

### `Database objects do not implement truth value testing`
If connecting to modern PyMongo (v4.0+), ensure connection checks use `if db is not None:` instead of `if db:`.

### HITL checkpoint stuck
SQLite checkpoint may be locked. Delete `data/blog_checkpoints.db` and restart.

## 📚 Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Tavily API](https://tavily.com/)
- [Dev.to API](https://developers.forem.com/api/)
- [Medium API](https://medium.com/me/settings/security)
- [Streamlit Docs](https://docs.streamlit.io/)

## 📄 License

MIT License — see LICENSE file

## 👥 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check existing documentation
- Review agent prompts in `src/llm/prompts.py`

---

**Built with ❤️ using LangGraph and Streamlit**
