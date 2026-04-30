# Historias de Usuario - Bot Telegram & Dashboard Admin

Este documento describe las funcionalidades del sistema desde la perspectiva de los diferentes tipos de usuarios, ajustado a la arquitectura empresarial actual.

## Perfil: Usuario Final (Telegram)

### HU01: Consulta de Información (Próximamente)
**Como** usuario interesado en los servicios de Interrapidisimo,
**quiero** hacer preguntas al bot de Telegram,
**para** obtener respuestas precisas sobre logística.
- **Estado Actual:** Desactivado temporalmente. El bot responde con un mensaje de espera mientras se escala la infraestructura de IA.

### HU02: Validación de Acceso Corporativo
**Como** colaborador de la empresa,
**quiero** que el bot valide mi identidad contra la base de datos centralizada de la compañía,
**para** asegurar que solo personal autorizado interactúe con el sistema.
- **Criterios de Aceptación:**
    - Al enviar `/start`, el sistema consulta la API externa configurada para verificar el teléfono.
    - Si el usuario no está en la base de datos corporativa, se deniega el acceso.

---

## Perfil: Administrador (Dashboard & Kong)

### HU03: Difusión Masiva de Mensajes
**Como** administrador del sistema,
**quiero** enviar mensajes de texto a múltiples canales de Telegram simultáneamente,
**para** informar sobre novedades operativas.
- **Criterios de Aceptación:**
    - Se seleccionan los canales desde la lista recuperada de la API externa.
    - Informe detallado de éxitos y fallos.

### HU04: Acceso Seguro Unificado (SSO)
**Como** administrador del Dashboard,
**quiero** iniciar sesión con mis credenciales corporativas directamente en la aplicación,
**para** mantener una experiencia de usuario fluida sin redirecciones externas.
- **Criterios de Aceptación:**
    - Formulario de login embebido en el Dashboard Angular.
    - Autenticación gestionada por Kong Enterprise.
    - Uso de cookies de sesión para mantener la conexión.

### HU05: Gestión de Canales Externos
**Como** administrador,
**quiero** que los canales disponibles para difusión sean consumidos de una API externa,
**para** evitar la duplicidad de datos y depender de archivos locales.
- **Criterios de Aceptación:**
    - Los canales se sincronizan automáticamente con la fuente de verdad empresarial.

### HU06: Auditoría y Seguridad Empresarial
**Como** responsable de seguridad,
**quiero** que el backend valide el token Bearer inyectado por el API Gateway,
**para** asegurar que todas las peticiones administrativas han sido autenticadas previamente por Kong.
- **Criterios de Aceptación:**
    - El backend rechaza cualquier petición que no provenga de un flujo autorizado.
    - Validación de JWT contra el servidor de Keycloak.

---

## Perfil: Desarrollador / DevOps

### HU07: Configuración de Entorno Robusta
**Como** desarrollador,
**quiero** que el sistema ignore variables de entorno obsoletas en el archivo .env,
**para** facilitar la transición entre versiones sin errores de validación de Pydantic.
- **Criterios de Aceptación:**
    - Uso de `extra='ignore'` en la configuración del sistema.
