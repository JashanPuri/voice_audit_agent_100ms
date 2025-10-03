# Voice Audit Agent - 100ms

FastAPI server for voice audit agent with 100ms integration.

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Server

```bash
python src/main.py
```

Or using uvicorn directly:

```bash
uvicorn src.main:app --reload
```

