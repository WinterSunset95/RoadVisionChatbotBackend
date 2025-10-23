# RoadGPT (backend)

This is the backend for the RoadGPT chatbot. Built with FastAPI.

## Setting up the developer environment

### Linux
1. Clone the repository:
```
git clone https://github.com/WinterSunset95/RoadVisionChatbotBackend && cd RoadVisionChatbotBackend
```
2. (Optional but recommended) Create a virtual environment:
```
python3 -m venv .venv
```
3. Activate the virtual environment:
```
source .venv/bin/activate
```
4. Install dependencies:
```
pip install -r requirements.txt
```
5. Run the startup script:
```
python app.py
```

### Windows
1. Clone the repository:
```
git clone https://github.com/WinterSunset95/RoadVisionChatbotBackend && cd RoadVisionChatbotBackend
```
2. (Optional but recommended) Create a virtual environment:
```
python -m venv .venv
```
3. Activate the virtual environment:
```
.\.venv\Scripts\activate
```
4. Install dependencies:
```
pip install -r requirements.txt
```
5. Run the startup script:
```
python app.py
```

## Requirements (Environment Variables, Credential files, etc.)

1. The following environment variables are required:
    - `GOOGLE_API_KEY`
    - `LLAMA_CLOUD_API_KEY`
    - `MONGO_INITDB_ROOT_USERNAME`
    - `MONGO_INITDB_ROOT_PASSWORD`
    - `MONGO_INITDB_DATABASE`
    - `MONGO_HOST`

2. The following credential files are required:
    - `credentials.json`: Google Drive API credentials
    - `token.json`: Google Drive API token

*Note: The application will absolutely NOT work without the above environment variables and credential files.*
*Please ask the developer for the files*
