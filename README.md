# Web OCR Tool

A Flask-based web application that captures screenshots of webpages, extracts text using OCR, and structures the data using AI.

## Features

- Take full-page screenshots of any webpage
- Extract text using EasyOCR
- Process and structure data using OpenAI's GPT-3.5
- Modern web interface with real-time progress updates
- Download structured data as CSV

## Prerequisites

- Python 3.7+
- Chrome browser (for Selenium)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Local Development

1. Start the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Deployment to Vercel

1. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. Deploy to Vercel:
   - Go to [Vercel](https://vercel.com)
   - Import your GitHub repository
   - Add the following environment variables in Vercel:
     - `OPENAI_API_KEY`: Your OpenAI API key
   - Deploy!

## Project Structure

- `app.py`: Main Flask application
- `tool.py`: Core OCR and data processing functionality
- `templates/`: HTML templates
- `screenshots/`: Directory for storing screenshots and chunks
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (create from .env.example)
- `vercel.json`: Vercel deployment configuration
- `runtime.txt`: Python runtime specification

## Notes

- The application uses EasyOCR for text extraction
- Screenshots are split into chunks for better processing
- Data structuring is done using OpenAI's GPT-3.5
- All screenshots and extracted data are stored in the `screenshots` directory
- Environment variables are used for sensitive configuration
- The application is configured for deployment on Vercel 