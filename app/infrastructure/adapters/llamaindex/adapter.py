import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from app.domain.ports.knowledge_base import KnowledgeBasePort

class LlamaIndexAdapter(KnowledgeBasePort):
    def __init__(self, api_key: str):
        # Configuraciones base para OpenAI
        Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key)
        
        # Paths (Subir 5 niveles para llegar a la raíz desde app/infrastructure/adapters/llamaindex/)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        self.persist_dir = os.path.join(self.base_dir, "storage")
        self.data_dir = os.path.join(self.base_dir, "data")
        
        self.query_engine = None

    def _init_index(self):
        if not os.path.exists(self.persist_dir):
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            
            input_files = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir) if os.path.isfile(os.path.join(self.data_dir, f))]
            
            if not input_files:
                raise ValueError(f"No se encontraron archivos para indexar en {self.data_dir}. Asegúrate de colocar tus manuales allí.")

            documents = SimpleDirectoryReader(input_files=input_files).load_data()
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=self.persist_dir)
        else:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            index = load_index_from_storage(storage_context)
            
        return index

    def setup(self):
        """Inicializa el motor de consultas."""
        index = self._init_index()
        self.query_engine = index.as_query_engine(similarity_top_k=3)

    def ask(self, question: str) -> str:
        if not self.query_engine:
            self.setup()
        
        response = self.query_engine.query(question)
        return str(response)
