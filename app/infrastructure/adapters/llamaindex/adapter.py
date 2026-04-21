import os
import tiktoken
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, PromptTemplate
from llama_index.core.settings import Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from app.domain.ports.knowledge_base import KnowledgeBasePort
from app.infrastructure.logging.logger import logger, log_token_cost


# ──────────────────────────────────────────────────────────────
# Precios gpt-4o-mini + text-embedding-3-small (USD por token)
# ──────────────────────────────────────────────────────────────
PRICE_INPUT_PER_TOKEN  = 0.150 / 1_000_000   # $0.150 / 1M tokens
PRICE_OUTPUT_PER_TOKEN = 0.600 / 1_000_000   # $0.600 / 1M tokens
PRICE_EMBED_PER_TOKEN  = 0.020 / 1_000_000   # $0.020 / 1M tokens


def _build_token_table(
    *,
    classifier_input: int,
    classifier_output: int,
    rag_input: int,
    rag_output: int,
    embed_tokens: int,
) -> str:
    """Construye una tabla ASCII con el consumo y costo de tokens."""
    total_input  = classifier_input + rag_input
    total_output = classifier_output + rag_output

    cost_cls  = (classifier_input * PRICE_INPUT_PER_TOKEN
                 + classifier_output * PRICE_OUTPUT_PER_TOKEN)
    cost_rag  = (rag_input * PRICE_INPUT_PER_TOKEN
                 + rag_output * PRICE_OUTPUT_PER_TOKEN)
    cost_emb  = embed_tokens * PRICE_EMBED_PER_TOKEN
    cost_total = cost_cls + cost_rag + cost_emb

    lines = [
        "\n╔══════════════════════════════════════════════════════════════╗",
        "║              CONSUMO DE TOKENS — ANÁLISIS DE COSTO           ║",
        "╠══════════════╦════════════╦═════════════╦═════════════════════╣",
        "║ Etapa        ║ Input tok. ║ Output tok. ║ Costo (USD)         ║",
        "╠══════════════╬════════════╬═════════════╬═════════════════════╣",
        f"║ Clasificador ║ {classifier_input:>10} ║ {classifier_output:>11} ║ ${cost_cls:>19.8f} ║",
        f"║ RAG / LLM    ║ {rag_input:>10} ║ {rag_output:>11} ║ ${cost_rag:>19.8f} ║",
        f"║ Embeddings   ║ {embed_tokens:>10} ║ {'—':>11} ║ ${cost_emb:>19.8f} ║",
        "╠══════════════╬════════════╬═════════════╬═════════════════════╣",
        f"║ TOTAL        ║ {total_input:>10} ║ {total_output:>11} ║ ${cost_total:>19.8f} ║",
        "╚══════════════╩════════════╩═════════════╩═════════════════════╝",
    ]
    return "\n".join(lines)


class LlamaIndexAdapter(KnowledgeBasePort):
    def __init__(self, api_key: str):
        try:
            # ── Token counter (comparte callback con Settings) ──
            self._token_counter = TokenCountingHandler(
                tokenizer=tiktoken.encoding_for_model("gpt-4o-mini").encode,
                verbose=False,
            )
            callback_manager = CallbackManager([self._token_counter])

            self._llm = OpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=api_key,
                callback_manager=callback_manager,
            )
            Settings.llm = OpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=api_key,
                callback_manager=callback_manager,
            )
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=api_key,
                callback_manager=callback_manager,
            )
            Settings.callback_manager = callback_manager

        except Exception as e:
            logger.error(f"Error configurando modelos de LlamaIndex: {e}")
            raise

        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        self.persist_dir = os.path.join(self.base_dir, "storage")
        self.data_dir    = os.path.join(self.base_dir, "data")

        self.query_engine = None

    # ──────────────────────────────────────────────
    # Mensaje estándar para preguntas fuera de tema
    # ──────────────────────────────────────────────
    OUT_OF_CONTEXT_MSG = (
        "Lo siento, solo puedo ayudarte con temas relacionados a Interrapidísimo: "
        "envíos, rastreo de guías, tarifas, sedes, servicios y PQR. "
        "¿En qué te puedo ayudar con eso?"
    )

    # ──────────────────────────────────────────────
    # ETAPA 1: Clasificador de intención con LLM
    # ──────────────────────────────────────────────
    def _is_relevant_query(self, question: str) -> bool:
        """
        Pregunta al LLM si la consulta tiene relación con el negocio
        de mensajería/logística/envíos. Retorna True si es relevante.
        """
        classifier_prompt = (
            "Eres un clasificador de intención para un chatbot de Interrapidísimo, "
            "empresa colombiana de mensajería y logística.\n\n"
            "Determina si la siguiente consulta del usuario está relacionada con "
            "ALGUNO de estos temas:\n"
            "- Envíos, paquetes, encomiendas, mercancías\n"
            "- Rastreo, seguimiento, validación o estado de un envío\n"
            "- Guías, números de guía\n"
            "- Tarifas, costos, cotizaciones\n"
            "- Sedes, oficinas, RACOL, direcciones, teléfonos\n"
            "- Servicios de la empresa (mensajería, carga, internacional)\n"
            "- Artículos permitidos o prohibidos para enviar\n"
            "- PQR, reclamos, garantías, indemnizaciones\n"
            "- Embalaje, peso, medidas\n"
            "- Atención al cliente de Interrapidísimo\n"
            "- Telefonos de las sedes, racoles o puntos de Interrapidísimo\n"
            "- Giros, envío de dinero, remesas\n\n"
            "IMPORTANTE: Sé FLEXIBLE. Si la consulta puede interpretarse como "
            "relacionada con envíos o logística (aunque use palabras coloquiales "
            "como 'mandar', 'despachar', 'validar', 'checar', 'ver', 'plata'), responde SÍ.\n\n"
            f"Consulta: \"{question}\"\n\n"
            "Responde ÚNICAMENTE con una sola palabra: SI o NO."
        )
        try:
            result = self._llm.complete(classifier_prompt)
            answer = str(result).strip().upper()
            is_relevant = answer.startswith("SI") or answer.startswith("SÍ")
            logger.info(f"Clasificador → '{answer}' para: '{question[:60]}'")
            return is_relevant
        except Exception as e:
            logger.warning(f"Error en clasificador, asumiendo relevante: {e}")
            return True

    # ──────────────────────────────────────────────
    # Inicialización del índice vectorial
    # ──────────────────────────────────────────────
    def _init_index(self):
        try:
            if not os.path.exists(self.persist_dir):
                logger.info("Iniciando indexador de RAG (Primera ejecución)...")
                if not os.path.exists(self.data_dir):
                    os.makedirs(self.data_dir)

                input_files = [
                    os.path.join(self.data_dir, f)
                    for f in os.listdir(self.data_dir)
                    if os.path.isfile(os.path.join(self.data_dir, f))
                ]

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

    # ──────────────────────────────────────────────
    # Configuración del motor de consultas
    # ──────────────────────────────────────────────
    def setup(self):
        """Inicializa el motor de consultas RAG."""
        try:
            qa_prompt_str = (
                "Eres un asistente virtual de Interrapidísimo, empresa colombiana de mensajería y logística.\n"
                "Tu función es ayudar a los clientes con información sobre envíos, rastreo, tarifas y servicios.\n\n"
                "La siguiente información de contexto ha sido extraída de los documentos oficiales:\n"
                "---------------------\n"
                "{context_str}\n"
                "---------------------\n\n"
                "INSTRUCCIONES:\n"
                "1. Usa el contexto anterior como tu fuente principal de información.\n"
                "2. Puedes interpretar preguntas coloquiales (ej: 'validar envío' = rastrear, "
                "'mandar algo' = hacer un envío, 'trago' = licor/bebida alcohólica).\n"
                "3. Si el contexto tiene información relevante aunque sea parcialmente, úsala para responder.\n"
                "4. Si la información NO está en el contexto y no puedes inferirla razonablemente "
                "del tema de logística/envíos, responde: "
                "'No tengo esa información específica, pero puedes contactarnos por la Línea Nacional: 323 254 0404.'\n"
                "5. Responde siempre en español, de forma clara y amigable.\n\n"
                "Pregunta del cliente: {query_str}\n"
            )
            qa_prompt_tmpl = PromptTemplate(qa_prompt_str)

            index = self._init_index()
            self.query_engine = index.as_query_engine(
                similarity_top_k=5,
                text_qa_template=qa_prompt_tmpl,
            )
            logger.info("Motor de consultas RAG listo.")
        except Exception as e:
            logger.error(f"No se pudo configurar el motor de consultas: {e}")
            raise

    # ──────────────────────────────────────────────
    # Punto de entrada principal
    # ──────────────────────────────────────────────
    def ask(self, question: str) -> str:
        try:
            if not self.query_engine:
                self.setup()

            # ── Reiniciar contadores antes de procesar ──
            self._token_counter.reset_counts()

            # ── ETAPA 1: Clasificador de intención ──
            if not self._is_relevant_query(question):
                logger.info(f"Pregunta descartada por clasificador: '{question[:60]}'")

                cls_in  = self._token_counter.prompt_llm_token_count
                cls_out = self._token_counter.completion_llm_token_count
                embed   = self._token_counter.total_embedding_token_count
                cost    = (cls_in * PRICE_INPUT_PER_TOKEN
                           + cls_out * PRICE_OUTPUT_PER_TOKEN
                           + embed * PRICE_EMBED_PER_TOKEN)

                table = _build_token_table(
                    classifier_input=cls_in, classifier_output=cls_out,
                    rag_input=0, rag_output=0, embed_tokens=embed,
                )
                logger.info(table)
                log_token_cost(
                    question=question,
                    cls_input=cls_in, cls_output=cls_out,
                    rag_input=0, rag_output=0,
                    embed_tokens=embed, cost_usd=cost,
                )
                return self.OUT_OF_CONTEXT_MSG

            # Guardar tokens del clasificador antes del RAG
            cls_input_tokens  = self._token_counter.prompt_llm_token_count
            cls_output_tokens = self._token_counter.completion_llm_token_count

            # ── ETAPA 2: RAG sobre los documentos ──
            logger.info(f"Procesando pregunta RAG: '{question[:50]}...'")
            response = self.query_engine.query(question)

            # Tokens del RAG = total acumulado - tokens del clasificador
            rag_input_tokens  = self._token_counter.prompt_llm_token_count  - cls_input_tokens
            rag_output_tokens = self._token_counter.completion_llm_token_count - cls_output_tokens
            embed_tokens      = self._token_counter.total_embedding_token_count

            cost_total = (
                (cls_input_tokens + rag_input_tokens) * PRICE_INPUT_PER_TOKEN
                + (cls_output_tokens + rag_output_tokens) * PRICE_OUTPUT_PER_TOKEN
                + embed_tokens * PRICE_EMBED_PER_TOKEN
            )

            table = _build_token_table(
                classifier_input=cls_input_tokens, classifier_output=cls_output_tokens,
                rag_input=rag_input_tokens, rag_output=rag_output_tokens,
                embed_tokens=embed_tokens,
            )
            logger.info(table)
            log_token_cost(
                question=question,
                cls_input=cls_input_tokens, cls_output=cls_output_tokens,
                rag_input=rag_input_tokens, rag_output=rag_output_tokens,
                embed_tokens=embed_tokens, cost_usd=cost_total,
            )

            return str(response).strip()

        except Exception as e:
            logger.error(f"Error durante la consulta RAG: {e}", exc_info=True)
            return "Lo siento, tuve un problema técnico al consultar mis manuales."
