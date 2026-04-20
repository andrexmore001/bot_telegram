# Documentación Técnica Detallada - Arquitectura Hexagonal

El bot utiliza un diseño de arquitectura limpia (Hexagonal) para asegurar que el núcleo de la aplicación sea independiente de las librerías externas y servicios de terceros.

## 1. Stack Tecnológico

- **Aiogram (v3.x)**: Framework asíncrono para el manejo de la API de Telegram. Actúa como un Adaptador de entrada.
- **LlamaIndex**: Motor de RAG para la ingestión y consulta de documentos. Actúa como un Adaptador de salida para la persistencia y búsqueda vectorial.
- **Dependency-Injector**: Librería para la gestión de Inyección de Dependencias (DI), facilitando el ensamblaje de componentes y el testing.
- **OpenAI**: Proveedor de LLM (`gpt-4o-mini`) y Embeddings (`text-embedding-3-small`).
- **Pydantic**: Validación de configuraciones y esquemas de datos.

## 2. Arquitectura del Sistema (Puertos y Adaptadores)

El sistema se divide en tres capas principales:

### A. Capa de Dominio (`app/domain`)
Es el corazón del sistema. Define las entidades de negocio y las interfaces (Puertos).
- **Puertos**: `KnowledgeBasePort` define cómo se debe interactuar con el cerebro del bot sin conocer si usa LlamaIndex, LangChain o una BD local.
- **Servicios**: `AssistantService` orquestra las operaciones principales.

### B. Capa de Infraestructura (`app/infrastructure`)
Contiene las implementaciones técnicas (Adaptadores).
- **Adaptadores**: Implementan los puertos del dominio (ej. `LlamaIndexAdapter`).
- **Telegram**: Gestiona la conexión y respuestas del bot de Telegram.
- **Contenedor**: El archivo `container.py` actúa como la fábrica que instancia y conecta todas las piezas.

### C. Capa de Aplicación (`main.py`)
Configura el entorno e inicia el ciclo de vida de la aplicación.

## 3. Flujo de Interacción RAG

1. **[Usuario]** envía un mensaje a Telegram.
2. **[Telegram Handler]** recibe el mensaje y lo pasa al **[AssistantService]**.
3. **[AssistantService]** usa el **[KnowledgeBasePort]**.
4. **[LlamaIndexAdapter]** (la implementación del puerto) realiza la búsqueda vectorial en `storage/`.
5. Se recupera el contexto, se envía a **OpenAI** y se obtiene la respuesta redactada.
6. La respuesta viaja de vuelta hasta el Usuario.

## 4. Inyección de Dependencias

El uso de `dependency-injector` permite que el sistema sea modular:
- Si mañana se desea cambiar OpenAI por Gemini, solo se cambia la implementación en el contenedor, sin tocar la lógica de los handlers ni del servicio de dominio.
