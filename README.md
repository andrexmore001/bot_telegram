# Proyecto: Telegram RAG Bot - Interrapidisimo PoC

Este proyecto es una Prueba de Concepto (PoC) de un bot de Telegram diseñado para servir como asistente virtual interactivo enfocado en logística. Implementa botones interactivos, flujos estructurados de conversación (Rastreo y PQRs) y un sistema avanzado de Retrieval-Augmented Generation (RAG) para responder de forma natural a consultas sobre conocimiento interno almacenado.

## 📂 Estructura de Carpetas e Índice del Proyecto.

A continuación se detalla exactamente para qué sirve cada componente del proyecto:

### 1. Directorio Raíz (`/`)
El directorio principal donde convergen todas las dependencias y la configuración de entrada.
- **`main.py`**: Es el archivo de orquestación principal. Arranca la instancia de FastAPI (para exponer la aplicación en un futuro mediante webhooks de forma asíncrona) y ejecuta el proceso de Long Polling del Bot de Telegram (Aiogram). Aquí se conectan los módulos del bot y del motor inteligente.
- **`requirements.txt`**: Listado de todas las librerías necesarias de Python (aiogram, llama-index, fastapi, etc.).
- **`.env` / `.env.example`**: Variables de entorno donde se almacenan y resguardan las llaves secretas (Telegram Bot Token y OpenAI API Key) dictando las credenciales necesarias.

### 2. Carpeta `/app`
Es el núcleo de la aplicación, separada mediante diseño estructurado.
- **`/app/bot`**: Contiene todo lo relacionado con la interfaz de interacción del usuario en Telegram.
  - `handlers.py`: Define cómo responde el bot ante ciertas palabras clave, estados actuales temporales, y presiones de botones (procesando "rastreos de guías", "PQRs" y derivando mensajes a LlamaIndex).
  - `states.py`: Almacena la arquitectura o flujos (State Machines - FSM) utilizados para rastrear exactamente en qué paso de una función secuencial se encuentra el usuario (por ejemplo, "esperando número de guía").
- **`/app/core`**: Funcionalidades transversales para todo el proyecto.
  - `config.py`: Gestor basado en Pydantic y `python-dotenv` encargado de parsear el archivo `.env` de forma segura, mapeandolo a un objeto `config` que se distribuye a cualquier archivo que solicite una variable global como la llave de OpenAI.
- **`/app/rag`**: Carpeta donde recae la lógica del "Cerebro" extraído usando Inteligencia Artificial.
  - `engine.py`: Encarga la configuración e inicialización de **LlamaIndex**, el Indexador Vectorial para RAG y el Motor de Consultas (Query Engine). Lee los documentos cargados, los vectoriza contra OpenAI si no existían antes y expone el método `ask_question(...)` que usa el bot.

### 3. Carpeta `/data`
El "Almacén de Conocimiento". Aquí debes soltar (en formato plano como `.txt`, `.pdf`, o `.csv`) la información viva del negocio o la empresa que deseas que sea inyectada al cerebro del bot. Por defecto, almacena `interrapidisimo_info.txt`.

### 4. Carpeta `/storage`
La base de datos vectorial en memoria persistida. Ésta carpeta es **auto-generada** por LlamaIndex (por ende puede reconstruirse desde cero). Almacena los "embeddings" (texto de OpenAI vectorizado a números) en formato JSON para no tener que incurrir en costos de procesamiento vectorial a OpenAI cada vez que se arranca el código.
