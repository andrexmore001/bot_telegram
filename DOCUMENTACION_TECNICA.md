# Documentación Técnica Detallada - Arquitectura y Flujos

A nivel tecnológico, el bot consolida su stack combinando procesamiento determinista con inteligencia contextual estocástica.

## 1. Stack Tecnológico

- **Aiogram (v3.x)**: El framework principal para el Bot de Telegram por excelencia al programar en Python asíncrono puro. Maneja `Routers` y `FSMContext` (Máquinas de Estados por parte del usuario) de manera escalable.
- **LlamaIndex**: Motor moderno para Ingestión y Procesamiento de datos (RAG - *Retrieval-Augmented Generation*). Capaz de ingerir PDFs y textos desestructurados para encajonarlos en índices en memoria. Es el encargado de responder cuando el bot no posee un "flujo de negocio determinista".
- **FastAPI**: Un microframework veloz y asíncrono para construir APIs. Su rol fundamental en este código es estar listo como *contenedor web*, actuando como ciclo de vida de la app (`lifespan`) y exponiendo *status endpoints*. Es fundamental por si algún día se transiciona desde Long-Polling hacia **Webhooks** en AWS o Vercel.
- **OpenAI**: Emplea el modelo rápido `text-embedding-3-small` para vectorización semántica espacial de los documentos, y usa `gpt-3.5-turbo` para resumir contextual al final y entablar conversación amigable de acuerdo a la búsqueda semántica vectorizada.

## 2. Diagrama de Arquitectura del Sistema

El siguiente comportamiento detalla el paso de cualquier mensaje escrito por un usuario externo:

**Flujo de interacciones:**
1. **[Usuario Telegram]** -> *(Envía Mensaje o Comando)* -> **[API de Telegram]**
2. **[API de Telegram]** 👉 *(Long Polling o Webhook)* 👉 **[Aiogram Handlers]**
3. El Gestor (Aiogram) decide la ruta:
   - **Ruta A (Comandos y Botones):** 👉 **[Flujos Deterministas FSM]** 👉 *(Simulación de API/BD)* 👉 Responde al Usuario.
   - **Ruta B (Texto Libre o Preguntas):** 👉 **[Módulo RAG con LlamaIndex]**
4. **En el Módulo RAG:** 
   - Consulta el índice vectorial: **[VectorStoreIndex local]**.
   - Recupera el texto más relevante y se lo envía a **[LLM: GPT-3.5]**.
   - El modelo de lenguaje redacta una respuesta inteligente 👉 Responde al Usuario.

## 3. Comportamiento RAG: Análisis a Bajo Nivel (`app/rag/engine.py`)

La función de LlamaIndex no interactúa con peticiones web, solo es consultada. 
Cuando se ejecuta la función `setup_rag()` o en su defecto recae la primera pregunta invocando un `ask_question()`:
1. **LlamaIndex escudriña el FileSystem**: Utilizando Python `os.listdir`, verifica el módulo `/data/` y encuentra (por ejemplo) `interrapidisimo_info.txt`.
2. **Creación del Indexador**: Toma el archivo, extrae todos sus párrafos y los divide en Trozos o "Chunks". Se los envía asíncronamente a los servidores de OpenAI a través de `text-embedding-3-small`. OpenAI devuelve matrices numéricas matemáticas de múltiples dimensiones.
3. **Punto de Persistencia (Vectorization Cache)**: Guarda todas esas matrices numéricas encriptadas dentro de un archivo base local `storage/default__vector_store.json`. Las próximas veces que se inicie el aplicativo, leerá este archivo y saltará el paso 2 ahorrando tiempo fundamental de cómputo/costo de red y API keys de OpenAI.
4. **Módulo Generativo (`gpt-3.5-turbo`)**: Cuando un usuario chatea "Oye quiero mandar un líquido", LlamaIndex vectoriza esa frase pequeña (Top K=3 de simulación vectorial), cruza la similitud vectorial de matemáticas de base de datos contra el trozo que habla de "líquidos y mercancía prohibida", extrae este contexto y se lo inyecta a un mensaje final que OpenAI modeliza a humano: "*De acuerdo a nuestras políticas las reglas dictan ...*"

## 4. Estructura de State Machines (`app/bot/states.py` y `handlers.py`)

La librería **Aiogram** utiliza el `FSMContext` de Llama. En el sistema hay un `InterrapidisimoFlow` que se comporta de la siguiente forma logíca para no mezclar variables globales entre sesiones simultaneas de usuarios (Escalamiento Asíncrono puro):
- Si el usuario dice "Rastrear", entramos en `State = waiting_for_tracking_number`. 
- Automáticamente el Bot se olvida de ser RAG por un instante y solo se concentrará en validar (con if/else) la longitud de la cadena que reciba en formato numérico (`message.text.isdigit()`). 
- Tras la validación rompe estado usando `.clear()` liberando los bytes de memoria del cache de asincronía.

## 5. Control de Ambientes (`app/core/config.py`)

Pydantic `BaseSettings` actúa preleyendo con fuerza rígida de tipos. Es una capa de seguridad moderna excelente de Python. Si tú olvidas proveer un `TELEGRAM_BOT_TOKEN`, la aplicación explotará directamente validando los requerimientos en la línea 1 en lugar de colgarse a la mitad de un proceso de red en ejecución.
