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

1. Install the required Python packages:

    ```bash
    cd backend
    python -m venv venv 
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2. Set up the PostgreSQL database:

    - Install PostgreSQL if not already installed
    - Create a new database for the project
    - Update the `.env` file in the `backend` directory with your database credentials:
    ```
    DATABASE_URL=postgresql://your_username:your_password@localhost:5432/your_database_name
    ```
3. Add your OpenAI API key:
    - Update the `.env` file in the `backend` directory
    - Add your OpenAI API key:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```
    
4. Run the database setup script after updating the database name in the setup.sql file:
   ```
   psql -d your_database_name -f backend/setup.sql
   ```
5. Start the backend server:
   ```
    uvicorn app.main:app --reload
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

