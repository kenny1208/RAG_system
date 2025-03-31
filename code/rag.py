from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import NLTKTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import nltk
import os
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv


console = Console()
#nltk.download('punkt')

load_dotenv()  
api_key = os.getenv("GOOGLE_API_KEY")

chat_model = ChatGoogleGenerativeAI(
    google_api_key=api_key,
    model="gemini-1.5-pro-latest"
)

loader = PyPDFLoader("../data/1neural_network.pdf")
pages = loader.load_and_split()

text_splitter = NLTKTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(pages)

embedding = GoogleGenerativeAIEmbeddings(google_api_key=api_key, model="models/embedding-001")

vectorstore = Chroma.from_documents(chunks, embedding)
retriever = vectorstore.as_retriever()

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are a teacher in Scaffolding Instruction education.
                  Given a context and question from user,
                  you should answer based on the given context."""),
    HumanMessagePromptTemplate.from_template("""Answer the question based on the given context.
    Context: {context}
    Question: {question}
    Answer: """)
])


chain = (
    {"context": retriever | RunnablePassthrough(), "question": RunnablePassthrough()}
    | prompt
    | chat_model
    | StrOutputParser()
)

while True:
    user_input = input("Write your question (or type 'exit' to quit): ")
    if user_input.lower() == 'exit':
        break
    result = chain.invoke(user_input)
    console.print(Markdown(f"\n{result}\n"))
    print("\n--------------------------\n")
