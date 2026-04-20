# Proyecto: Telegram RAG Bot - Interrapidisimo PoC

Este proyecto es una Prueba de Concepto (PoC) de un bot de Telegram diseñado para servir como asistente virtual inteligente. Utiliza una **Arquitectura Hexagonal** (Puertos y Adaptadores) para mantener un núcleo de negocio desacoplado y un sistema avanzado de **Retrieval-Augmented Generation (RAG)** para responder de forma natural a consultas sobre conocimiento interno almacenado.

## 📂 Estructura del Proyecto (Arquitectura Hexagonal)

A continuación se detalla la organización del código basada en capas de responsabilidad:

### 1. Directorio Raíz (`/`)
- **`main.py`**: Punto de entrada de la aplicación. Configura la inyección de dependencias y arranca el bot de Telegram en modo Long Polling.
- **`requirements.txt`**: Librerías necesarias (aiogram, llama-index, dependency-injector, etc.).
- **`.env`**: Archivo de configuración para tokens de Telegram y OpenAI.

### 2. Carpeta `/app`
Organizada en capas de diseño limpio:
- **`/app/domain`**: El núcleo de la aplicación.
  - `models/`: Definiciones de datos puros.
  - `ports/`: Interfaces que definen los contratos que la infraestructura debe cumplir (ej. `KnowledgeBasePort`).
  - `services/`: Lógica de negocio orquestadora (`AssistantService`).
- **`/app/infrastructure`**: Adaptadores y configuraciones técnicas.
  - `adapters/`: Implementaciones concretas de los puertos (Telegram con Aiogram, RAG con LlamaIndex).
  - `config/`: Gestión de variables de entorno mediante Pydantic.
  - `container.py`: Contenedor de Inyección de Dependencias que ensambla el sistema.

### 3. Carpeta `/data`
El "Almacén de Conocimiento". Aquí debes colocar los archivos (`.txt`, `.pdf`, `.csv`) con la información del negocio que deseas que la IA aprenda.

### 4. Carpeta `/storage`
Base de datos vectorial persistida. Contiene los "embeddings" generados por OpenAI para evitar re-procesar los documentos en cada inicio, optimizando costos y tiempo.
