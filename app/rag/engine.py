import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from app.core.config import config

# Configuraciones base para OpenAI
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3, api_key=config.openai_api_key)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=config.openai_api_key)

# Calculate absolute paths relative to root directory (where main.py is)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = os.path.join(BASE_DIR, "storage")
DATA_DIR = os.path.join(BASE_DIR, "data")

def init_index():
    """
    Inicializa el índice de LlamaIndex.
    Si ya existe un almacenamiento persistente, lo carga.
    Si no, lee los documentos en ./data y crea el índice.
    """
    if not os.path.exists(PERSIST_DIR):
        print("Creando índice RAG desde cero...")
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # Busca todos los documentos validos en DATA_DIR para evadir errores de fsspec en Windows
        input_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        
        # Crea el índice
        index = VectorStoreIndex.from_documents(documents)
        
        # Guarda el índice de forma persistente
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        print("Cargando índice RAG existente...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
        
    return index

def get_query_engine():
    """Retorna un motor de consultas (query engine) listo para usar."""
    index = init_index()
    # Usamos retriever para buscar datos y generador para responder
    return index.as_query_engine(similarity_top_k=3)

# Inicializamos el engine de manera global
query_engine = None

def setup_rag():
    global query_engine
    query_engine = get_query_engine()

def ask_question(question: str) -> str:
    """Interroga al RAG sobre una pregunta."""
    if not query_engine:
        setup_rag()
    
    response = query_engine.query(question)
    return str(response)
