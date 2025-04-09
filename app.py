from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import NLTKTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from dotenv import load_dotenv
import nltk

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['VECTOR_DB_DIR'] = 'vectordbs'  # Directory to store vector databases
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['VECTOR_DB_DIR'], exist_ok=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Download NLTK data
nltk.download('punkt')

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_pdfs(file_paths, session_id):
    """Process PDF files and return chunks and a summary"""
    # Load PDFs
    all_pages = []
    for path in file_paths:
        filename = os.path.basename(path)
        loader = PyPDFLoader(path)
        pages = loader.load_and_split()
        
        # Add source filename and page number to metadata
        for i, page in enumerate(pages):
            page.metadata["source"] = filename
            page.metadata["page"] = i + 1  # Add page number (1-indexed)
        
        all_pages.extend(pages)
    
    # Split text into chunks
    text_splitter = NLTKTextSplitter(chunk_size=1500, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_pages)
    
    # Create embeddings and vectorstore
    embedding = GoogleGenerativeAIEmbeddings(google_api_key=api_key, model="models/embedding-001")
    
    # Create a persistent Chroma DB with the session ID as the collection name
    persist_directory = os.path.join(app.config['VECTOR_DB_DIR'], session_id)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=persist_directory,
        collection_name=session_id
    )
    vectorstore.persist()  # Save to disk
    
    # Create summary
    chat_model = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model="gemini-1.5-pro-latest"
    )
    
    summary_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a helpful assistant that summarizes technical documents."),
        HumanMessagePromptTemplate.from_template("""Summarize the following content into a bullet-point outline for review:

{context}

Summary:""")
    ])

    summary_chain = (
        RunnablePassthrough()
        | (lambda docs: {"context": "\n\n".join([d.page_content for d in docs])})
        | summary_prompt
        | chat_model
        | StrOutputParser()
    )
    
    summary = summary_chain.invoke(chunks)
    
    return chunks, summary

def get_vectorstore(session_id):
    """Retrieve the vectorstore for the given session ID"""
    persist_directory = os.path.join(app.config['VECTOR_DB_DIR'], session_id)
    embedding = GoogleGenerativeAIEmbeddings(google_api_key=api_key, model="models/embedding-001")
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding,
        collection_name=session_id
    )
    return vectorstore

def format_sources(retrieved_docs):
    """Format the retrieved documents into context and sources"""
    context_content = []
    sources = []
    
    for doc in retrieved_docs:
        context_content.append(doc.page_content)
        
        # Extract source information
        source = doc.metadata.get("source", "Unknown source")
        page = doc.metadata.get("page", "Unknown page")
        
        # Add to sources if not already present
        source_citation = f"{source} (page {page})"
        if source_citation not in sources:
            sources.append(source_citation)
    
    return {
        "context": "\n\n".join(context_content),
        "sources": sources
    }

def get_answer(session_id, question):
    """Get an answer to a question using the retriever"""
    vectorstore = get_vectorstore(session_id)
    
    chat_model = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model="gemini-1.5-pro-latest"
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5}  # Retrieve top 5 documents for better context
    )
    
    # Create a formatted retriever that returns context and sources
    def retrieve_and_format(question):
        docs = retriever.invoke(question)
        return format_sources(docs)
    
    formatted_retriever = RunnableLambda(retrieve_and_format)
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a helpful assistant that answers questions based on the provided context.
        You will be given a context and a question. Provide a comprehensive and accurate answer based on the context.
        
        Important: When you use information from the context, cite the source documents by including the document name and page number in 
        brackets at the end of the relevant sentence or paragraph. For example: [Document.pdf (page 5)].
        
        If the context doesn't contain enough information to answer the question, say so clearly and don't make up information."""),
        HumanMessagePromptTemplate.from_template("""Answer the question based on the given context.
        
        Context: {context}
        
        Question: {question}
        
        Answer: """)
    ])
    
    # Use RunnableLambda to properly combine the question and context
    def combine_context_and_question(inputs):
        return {
            "context": inputs["retrieved"]["context"],
            "question": inputs["question"]
        }
    
    chain = (
        {"question": RunnablePassthrough(), "retrieved": formatted_retriever}
        | RunnableLambda(combine_context_and_question)
        | prompt
        | chat_model
        | StrOutputParser()
    )
    
    # Get the result
    answer = chain.invoke(question)
    
    # Get sources for the reference list
    retrieved_info = formatted_retriever.invoke(question)
    sources = retrieved_info["sources"]
    
    return {
        "answer": answer,
        "sources": sources
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    # Create session directory
    session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_dir, filename)
            file.save(file_path)
            file_paths.append(file_path)
    
    if not file_paths:
        return jsonify({'error': 'No valid PDF files uploaded'}), 400
    
    try:
        chunks, summary = process_pdfs(file_paths, session_id)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'message': f'Successfully processed {len(file_paths)} files with {len(chunks)} chunks of content'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No documents have been uploaded yet'}), 400
    
    # Check if vector DB exists for this session
    vector_db_path = os.path.join(app.config['VECTOR_DB_DIR'], session_id)
    if not os.path.exists(vector_db_path):
        return jsonify({'error': 'No documents have been processed yet'}), 400
    
    try:
        result = get_answer(session_id, question)
        return jsonify({
            'answer': result["answer"],
            'sources': result["sources"]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)