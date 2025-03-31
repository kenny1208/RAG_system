# Gemini RAG Scaffolding QA System

A simple yet powerful Retrieval-Augmented Generation (RAG) system using **LangChain**, **Google Gemini**, and **PDF documents** — designed for educational applications, especially **Scaffolding Instruction**.

> Ask questions based on multiple PDF files and get intelligent, context-aware answers!

---

## Features

- Load multiple PDF files automatically
- Uses LangChain + Google Generative AI (`gemini-1.5-pro-latest`)
- Embedding powered by `models/embedding-001`
- Interactive Q&A loop via terminal
- Clean output formatted in **Markdown**
- API key is safely stored using `.env` file

---

## Tech Stack

- Python 3.10+
- [LangChain](https://github.com/langchain-ai/langchain)
- [Google Generative AI (Gemini)](https://ai.google.dev/)
- [Chroma VectorStore](https://github.com/chroma-core/chroma)
- PDF Loader via `langchain_community`
- `python-dotenv` for environment variable
- `rich` for Markdown terminal output

---
