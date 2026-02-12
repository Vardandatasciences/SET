# Quick Setup Guide

## Step 1: Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Upgrade pip and install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install wheel
   pip install -r requirements.txt
   ```
   
   **Note:** The requirements.txt file is configured to let FastAPI automatically install a compatible version of pydantic with pre-built wheels, avoiding Rust compilation issues.
   
   **If installation still fails:**
   - Make sure you're using Python 3.9 or higher (Python 3.13 is supported)
   - Try installing packages individually if needed
   - The pydantic package will be installed automatically by FastAPI

5. **Create `.env` file:**
   Create a file named `.env` in the `backend` directory with:
   ```env
   PERPLEXITY_API_KEY=your_actual_perplexity_api_key_here
   API_HOST=0.0.0.0
   API_PORT=8000
   ```
   **Important:** Replace `your_actual_perplexity_api_key_here` with your actual Perplexity API key.

6. **Start the backend server:**
   ```bash
   python main.py
   ```
   Or use the startup script:
   - Windows: `start_server.bat`
   - Linux/Mac: `./start_server.sh`

   The backend should now be running at `http://localhost:8000`

## Step 2: Frontend Setup

1. **Open a new terminal and navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend should now be running at `http://localhost:3000`

## Step 3: Using the Application

1. Open your browser and go to `http://localhost:3000`
2. Select whether you want to research an **Individual** or **Organization**
3. Enter the name (e.g., "Microsoft Corporation" or "Satya Nadella")
4. Choose your preferred output format (Word, PDF, or PowerPoint)
5. Click "Generate Intelligence Capsule"
6. Wait for the research to complete (this may take 30-60 seconds)
7. Review the results and click "Download" to get your document

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure you've activated the virtual environment and installed all requirements
- **API key errors**: Verify your `.env` file exists and contains a valid Perplexity API key
- **Port already in use**: Change the port in `.env` or stop the process using port 8000
- **Rust/Cargo compilation errors (pydantic-core)**: 
  - The requirements.txt is configured to let FastAPI install pydantic automatically, which includes a compatible pydantic-core with pre-built wheels
  - If you still get errors, make sure pip and wheel are up to date: `pip install --upgrade pip wheel`
  - Python 3.13 is fully supported with pre-built wheels for all packages
- **401 Authorization Required (Perplexity API)**: 
  - See `backend/TROUBLESHOOTING.md` for detailed steps
  - Common causes: invalid API key, expired key, insufficient credits, IP restrictions
  - Run `python check_config.py` in the backend directory to verify your API key is set correctly

### Frontend Issues

- **Cannot connect to backend**: Ensure the backend is running on port 8000
- **CORS errors**: Check that the backend CORS settings include `http://localhost:3000`

### PDF Generation

- PDF generation requires LibreOffice or pandoc to be installed
- If PDF conversion fails, the system will still generate a Word document
- You can manually convert Word documents to PDF using Microsoft Word or online converters

## Getting Your Perplexity API Key

1. Go to [Perplexity AI](https://www.perplexity.ai/)
2. Sign up or log in
3. Navigate to API settings
4. Generate a new API key
5. Copy the key and paste it into your `.env` file

## Notes

- The first research request may take longer as the system fetches comprehensive data
- Generated documents are saved in `backend/output/` directory
- The tool provides balanced intelligence including both positive developments and challenges

