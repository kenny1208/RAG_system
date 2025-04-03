# 📘 PDF RAG Assistant

A web-based application that enables users to upload PDF documents, automatically generates a summary of their content, and allows interactive question answering using a Retrieval-Augmented Generation (RAG) pipeline powered by Google's Gemini models.

## ✨ Features

- 📄 Upload and process multiple PDF files
- 📝 Automatic document summarization
- 💬 Ask questions about the documents
- ⚡ Fast and interactive Q&A system
- 🎨 Responsive and modern UI (HTML/CSS/JS)

## 🖥️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **AI Model**: LangChain + Google Generative AI (Gemini 1.5 Pro)
- **Embeddings**: Google Generative AI Embeddings
- **Vector Store**: Chroma DB
- **PDF Parsing**: LangChain PDF Loader

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google API Key for Gemini (set in `.env`)

### Installation

1. Clone the repo:

```bash
git clone https://github.com/kenny1208/RAG_system.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your API key in a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

4. Run the Flask app:

```bash
python app.py
```

## 🗃️ Project Structure

```
.
├── app.py                # Flask backend
├── code/
│   └── rag.py                # CLI testing script (RAG logic)
├── templates/
│   └── index.html        # Main web page
├── static/
│   ├── css/
│   │   └── styles.css    # Styles
│   └── js/
│       └── main.js       # Frontend interactivity
├── uploads/              # Temporary uploaded files
├── vectordbs/            # Persistent vector storage
├── .env                  # API keys and config (not committed)
```

## 📦 API Endpoints

- `GET /` – Web interface
- `POST /upload` – Upload PDFs and generate summary
- `POST /ask` – Ask a question about uploaded documents

## 🛡️ Environment Variables

| Variable         | Description                       |
| ---------------- | --------------------------------- |
| `GOOGLE_API_KEY` | Your Google Generative AI API Key |

## ✅ To-Do

- [ ] Support other file types (e.g., DOCX)
- [ ] Add citations and sources to answers

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.
