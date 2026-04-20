import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from app.domain.ports.knowledge_base import KnowledgeBasePort
from app.infrastructure.logging.logger import logger

class LlamaIndexAdapter(KnowledgeBasePort):
    def __init__(self, api_key: str):
        # Configuraciones base para OpenAI
        try:
            Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)
            Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key)
        except Exception as e:
            logger.error(f"Error configurando modelos de LlamaIndex: {e}")
            raise
        
        # Paths (Subir 5 niveles para llegar a la raíz desde app/infrastructure/adapters/llamaindex/)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        self.persist_dir = os.path.join(self.base_dir, "storage")
        self.data_dir = os.path.join(self.base_dir, "data")
        
        self.query_engine = None

    def _init_index(self):
        try:
            if not os.path.exists(self.persist_dir):
                logger.info("Iniciando indexador de RAG (Primera ejecución)...")
                if not os.path.exists(self.data_dir):
                    os.makedirs(self.data_dir)
                
                input_files = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir) if os.path.isfile(os.path.join(self.data_dir, f))]
                
                if not input_files:
                    raise ValueError(f"No se encontraron archivos en {self.data_dir}")

                documents = SimpleDirectoryReader(input_files=input_files).load_data()
                index = VectorStoreIndex.from_documents(documents)
                index.storage_context.persist(persist_dir=self.persist_dir)
                logger.info("Indexado completado y persistido en 'storage/'.")
            else:
                logger.info("Cargando índice vectorial desde cache ('storage/')...")
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                index = load_index_from_storage(storage_context)
                
            return index
        except Exception as e:
            logger.error(f"Error fatal inicializando el índice RAG: {e}", exc_info=True)
            raise

    def setup(self):
        """Inicializa el motor de consultas."""
        try:
            index = self._init_index()
            self.query_engine = index.as_query_engine(similarity_top_k=3)
            logger.info("Motor de consultas RAG listo.")
        except Exception as e:
            logger.error(f"No se pudo configurar el motor de consultas: {e}")
            raise

    def ask(self, question: str) -> str:
        try:
            if not self.query_engine:
                self.setup()
            
            logger.info(f"Procesando pregunta RAG: '{question[:50]}...'")
            response = self.query_engine.query(question)
            return str(response)
        except Exception as e:
            logger.error(f"Error durante la consulta RAG: {e}", exc_info=True)
            return "Lo siento, tuve un problema técnico al consultar mis manuales."
