==============================================================================
AI KNOWLEDGE ASSISTANT - DOCKER DISTRIBUTION PACKAGE
Enterprise Document RAG Platform (FastAPI + Streamlit + ChromaDB + SQLite)
Docker Hub: https://hub.docker.com/repositories/thamizhprabha
==============================================================================

QUICK START GUIDE (WINDOWS)
---------------------------

PREREQUISITES:
1. Docker Desktop for Windows installed and running:
   Download: https://www.docker.com/products/docker-desktop/
   (Make sure WSL 2 is enabled during Docker Desktop installation)

HOW TO RUN:
1. Extract this folder anywhere on your computer.
2. (Optional) Open '.env' in Notepad and enter your Google Gemini or OpenAI API key:
   - GEMINI_API_KEY=your_key_here
   (If you do not set an API key, the assistant will prompt you inside the UI Settings page).
3. Double-click 'start.bat'.
4. Docker will download the pre-built images and launch both services automatically.
5. Your browser will automatically open:
   - Web Application:  http://localhost:8501
   - Backend API Docs: http://localhost:8000/docs
   - Health Check:     http://localhost:8000/health

MANAGEMENT SCRIPTS:
- start.bat    : Starts the application in the background and opens your browser.
- stop.bat     : Gracefully stops all containers without deleting your stored data.
- restart.bat  : Reboots the frontend and backend containers.
- backup.bat   : Creates a timestamped backup of your SQLite database and ChromaDB vectors.

DATA PERSISTENCE & PRIVACY:
- All uploaded documents, chat conversations, and vector embeddings are stored
  securely in Docker persistent volumes ('rag_sqlite_data' and 'rag_chroma_data')
  on your local machine.
- Stopping or restarting the containers NEVER deletes your uploaded documents or chat history.
- No documents or private data are ever sent outside your machine, except prompts
  sent to your configured cloud LLM provider (Google Gemini or OpenAI).

TROUBLESHOOTING:
- If 'start.bat' says Docker is not running:
  Launch Docker Desktop from your Start menu and wait for the status bar icon to turn green.
- To view live backend and frontend logs:
  Open PowerShell in this folder and run:
  docker compose logs -f
- Default Ports:
  Frontend: 8501
  Backend:  8000
  If these ports are used by other apps, edit 'docker-compose.yml' to map different host ports.

==============================================================================
Published by: thamizhprabha
==============================================================================
