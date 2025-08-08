# 🤖 AI-Powered Natural Language SQL Query App

This project is a Flask-based web application that lets users ask natural language questions about their MySQL database. It uses **Google Gemini AI** to convert user input into SQL queries, fetches results from the MySQL database, and responds in friendly, conversational language.

---

## 🌟 Features

- Natural Language → SQL query conversion using **Gemini AI**
- Supports **SELECT** queries only (secure and read-only)
- Clean, user-friendly web UI with example prompts
- Converts raw SQL results into plain English
- Uses `mysql.connector` for DB interactions
- Converts `Decimal` and `datetime` values to readable formats
- Auto handles schema mapping and fuzzy department name matching (e.g. "agriculture" → "कृषी विभाग")

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-chatbot.git
cd ai-chatbot
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```


### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
or

```bash
pip install Flask mysql-connector-python python-dotenv google-generativeai markdown
```

### 4. Run the Application
```bash
python main.py
```

