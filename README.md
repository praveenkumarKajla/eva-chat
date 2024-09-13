# AI Chat Application

This project consists of a React frontend with TypeScript (using Vite) and a FastAPI backend.

## Frontend

The frontend is built using Vite with React and TypeScript.

To run the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Backend

The backend is built using FastAPI.

To run the backend:

```bash
cd backend
python -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Running the Application

To run the application, start the backend and frontend servers:

```bash
cd backend
uvicorn main:app --reload
```

```bash
cd frontend
npm run dev
```

Open your browser and navigate to `http://localhost:5173` to access the application.

