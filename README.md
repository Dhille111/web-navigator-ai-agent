# web-navigator-ai-agent

## 🚀 Problem Statement
Build an AI Agent that can take natural language instructions and autonomously drive the web using browser automation (Playwright/Selenium).  
Example:  
> "Search for laptops under 50k and list top 5."

The agent should parse instructions, control a browser, extract useful results, and return them in a structured format.

---

## 💡 Our Solution
We built an **AI-powered Web Navigator** that:
1. Accepts natural language commands from the user.
2. Parses intent + filters into a structured **action plan**.
3. Uses **Playwright automation** to perform the task on the web.
4. Returns **structured results** (title, price, link, snippet).
5. Displays results in a simple web interface with table view and CSV/JSON export.

---

## ✨ Unique Features
- 🗣️ **Voice Command Support (Prototype)**: Speak instead of typing instructions.  
- 🧩 **Multi-step Workflow Execution**: (Planned) Ability to chain tasks like *“Search laptops under 50k → open first result → scrape specifications”*.  
- 📊 **Downloadable Results**: Export results as **CSV/JSON** for easy sharing.  
- ⚡ **Smart Filters**: Automatically detect keywords like *under 50k*, *top 10*, *cheapest*, *latest*.  
- 🔄 **Cross-Site Search (Future)**: Aggregates results from multiple sources (Google, Amazon, Flipkart).  
- 🕵️ **Explainable Plan**: Shows the extracted **plan** before running automation (e.g., `{"intent": "search", "subject": "laptops", "price<50000", "top": 5}`).  
- 🌙 **Dark Mode UI**: Simple toggle for better UX during demo.  

---

## 🛠️ Tech Stack
- **Backend:** Python + FastAPI  
- **Frontend:** React (Vite)  
- **Browser Automation:** Playwright  
- **Instruction Parsing:** Rule-based parser + (optional) Local LLM (Ollama/LangChain)  
- **Deployment:** Local environment for demo  

---

## 👥 Team Members
- Member 1 – Project Lead & Integrator  
- Member 2 – Frontend (UI/UX, command input, results table)  
- Member 3 – Backend (FastAPI APIs)  
- Member 4 – Browser Automation (Playwright scripts)  
- Member 5 – Parser + Docs/Video Pitch  

---

## 🔑 Features (MVP)
- ✅ Accepts natural language command  
- ✅ Parses into intent + filters  
- ✅ Automates search with Playwright  
- ✅ Returns top N structured results (title, link, snippet)  
- ✅ Displays results in table + export option  

---

## 🔮 Future Scope
- Full **voice interaction** (speech-to-text + text-to-speech).  
- **Advanced multi-step workflows** (navigate, click, scrape deeper).  
- **Product comparisons** (side-by-side specs).  
- **Real-time monitoring** (*“Notify me when price drops below 40k”*).  
- **Browser-in-VM sandbox** for secure automation.  

---

## 🖥️ How to Run

### Backend
```bash
# Navigate to backend folder
cd backend

# Install dependencies
pip install fastapi uvicorn playwright

# Install browsers for Playwright
playwright install

# Run the backend server
uvicorn server:app --reload --port 8000
