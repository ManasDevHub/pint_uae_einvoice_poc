---
description: Start UAE E-Invoice Development Environment (Backend, Frontend, and Ngrok)
---

# 🚀 Starting the UAE E-Invoice Dev Environment

Follow these steps to run the full stack locally and expose it via **ngrok** for external testing.

## Prerequisites
- **Python 3.11** (for the backend)
- **Node.js 20+** (for the frontend)
- **Ngrok Account** (with authtoken configured)

## Step 1: Start the Backend (FastAPI)
Open a new terminal in the project root and run:
```powershell
# Activate venv (Windows)
.\venv\Scripts\activate

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Local URL**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

## Step 2: Start the Frontend (React/Vite)
Open another terminal, navigate to the `frontend` folder, and run:
```powershell
cd frontend
npm install  # (Only needed if you haven't run it yet)
npm run dev
```
- **Local URL**: `http://localhost:5173`
- **Proxy**: Dev server automatically proxies `/api`, `/auth`, etc., to port 8000.

## Step 3: Start Ngrok (Expose the App)
To share your app with others while keeping `localhost` working, open a third terminal in the root and run:
```powershell
.\ngrok.exe http 5173
```
- **Public URL**: Find the `Forwarding` URL in the terminal (e.g., `https://xxxx-xxx.ngrok-free.dev`).
- **Simultaneous Access**: You can now access the app at **both** `localhost:5173` and the ngrok URL.

---

### 💡 Pro Tip: Running Both Simultaneously
`ngrok` does not capture or "steal" the port. It simply forwards traffic from its public servers to your local machine.

| Access Point | Use Case |
| :--- | :--- |
| **Localhost:5173** | Quick testing & coding (fastest performance). |
| **Ngrok URL** | Mobile testing, sharing with clients, or testing external webhooks. |

---

### Troubleshooting
- **Ngrok Authtoken Error**: Run `.\ngrok.exe config add-authtoken <YOUR_TOKEN>` once.
- **Port 5173 Already in Use**: If Vite fails to start, run `npx kill-port 5173` or restart VS Code.
- **Backend Error**: Ensure you are in the project root and your virtual environment is active if you have one.
