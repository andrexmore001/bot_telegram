# Documentación Técnica Detallada - Arquitectura Hexagonal Híbrida

El sistema utiliza un diseño de arquitectura limpia (Hexagonal) evolucionado hacia un modelo híbrido que integra un **Bot de Telegram** y una **API REST Administrativa (Dashboard)**, asegurando que el núcleo de la aplicación sea independiente de las librerías externas.

## 1. Stack Tecnológico

- **Aiogram (v3.x)**: Framework asíncrono para el manejo de la API de Telegram. Actúa como un Adaptador de entrada para el usuario final.
- **FastAPI**: Servidor web de alto rendimiento utilizado para la capa administrativa y el Dashboard.
- **Dependency-Injector**: Gestión de Inyección de Dependencias (DI) centralizada en `container.py`.
- **Kong Enterprise**: API Gateway que gestiona la autenticación (Cookies a Tokens) y actúa como intermediario para el consumo de datos externos.
- **Keycloak**: Identity Provider utilizado por Kong para validar las credenciales del usuario.
- **Pydantic**: Validación de configuraciones y esquemas de datos (Settings y API Models).

## 2. Arquitectura del Sistema (Puertos y Adaptadores)

El sistema se divide en tres capas principales, manteniendo el desacoplamiento:

### A. Capa de Dominio (`app/domain`)
- **Puertos**: `UserRepositoryPort` (gestión de acceso y canales). Define la interfaz para interactuar con la fuente de datos externa.
- **Servicios**: `AssistantService` orquestra la lógica de respuesta del bot.

### B. Capa de Infraestructura (`app/infrastructure`)
- **Adaptadores de Entrada**:
    - `TelegramHandler`: Gestiona mensajes, comandos y callbacks de Telegram.
    - `AdminRouter`: Define los endpoints REST para la gestión de canales, usuarios y configuración.
- **Adaptadores de Salida**:
    - `ApiRepository`: Implementación que consume una API externa vía Kong para obtener usuarios autorizados (`Authorize_user`) y canales registrados.
- **Seguridad**:
    - `AccessControlMiddleware`: Filtra usuarios de Telegram basados en la lista blanca recuperada de la API.
    - `AuthService`: Valida los tokens JWT inyectados por Kong en el header `Authorization`.

### C. Capa de Aplicación (`main.py`)
Configura el entorno e inicia simultáneamente el ciclo de vida de FastAPI y el Polling del Bot de Telegram mediante tareas asíncronas de Python (`asyncio`).

## 3. Flujos de Trabajo

### Flujo de Datos (Whitelisting y Canales)
1. El sistema arranca y el `ApiRepository` consulta el endpoint de datos configurado.
2. La lista de usuarios y canales se mantiene sincronizada con la fuente de verdad externa.
3. El Bot utiliza esta información para permitir o denegar el acceso a los comandos.

### Flujo Administrativo (Kong Gateway + Frontend Angular)
1. **Login Embebido**: El usuario ingresa credenciales en el Dashboard (Angular).
2. **Autenticación**: El Frontend envía `POST /api/auth/login` a Kong. Kong valida contra Keycloak y devuelve una **Cookie de Sesión**.
3. **Inyección de Identidad**: En cada petición posterior del Dashboard, Kong recibe la cookie, la traduce a un token JWT e inyecta el header `Authorization: Bearer <token>` hacia el Backend.
4. **Validación JWT**: El Backend (FastAPI) valida la firma del token inyectado para autorizar la operación.

## 4. Estado de la IA (RAG)
> [!NOTE]
> Las funcionalidades de Inteligencia Artificial (LlamaIndex/OpenAI) se encuentran **desactivadas temporalmente** para esta versión. El `AssistantService` entrega respuestas predefinidas mientras se escala la infraestructura.

## 5. Observabilidad y Errores
- **Logging**: Implementación de un logger centralizado que registra tanto eventos del bot como tráfico de la API y tiempos de respuesta.
- **Manejo de Errores**: Handlers globales para capturar excepciones en la API (FastAPI) y en el flujo del bot (Aiogram Errors).
