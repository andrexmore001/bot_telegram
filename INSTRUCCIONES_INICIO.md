# Manual de Inicio: ¿Cómo Ejecutar el Bot y la API?

Sigue este tutorial paso a paso para levantar correctamente el proyecto (Bot + Dashboard API) en tu entorno de desarrollo, integrado con Kong Enterprise.

## Prerrequisitos

- Python 3.10 o superior.
- Bot de Telegram (Token de `@BotFather`).
- Acceso a Kong Enterprise y Keycloak.
- API Key de OpenAI (Aunque la IA esté desactivada, el adapter la requiere para instanciarse).

---

## Paso 1: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente formato:

```env
# Credenciales Básicas
TELEGRAM_BOT_TOKEN="tu-token-telegram-aqui"
OPENAI_API_KEY="sk-proj-tu-llave-openai-aqui"

# Configuración Administrativa (Keycloak & Kong)
KEYCLOAK_URL="https://tu-keycloak.com/auth"
KEYCLOAK_REALM="tu-realm"
KEYCLOAK_AUDIENCE="ApiTelegramProd"

# Fuente de Datos Externa (Vía Kong)
EXTERNAL_DATA_API_URL="https://konge-dev.interrapidisimo.co/api/v1/data"

# IDs de Telegram (Opcionales para flujos específicos)
VIP_CHANNEL_ID="-100xxxxxxxxx"
VIP_GROUP_ID="-100xxxxxxxxx"
```

---

## Paso 2: Instalación y Ejecución

**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**En MacOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Paso 3: Acceso a las Interfaces

### 1. Bot de Telegram
Busca tu bot en Telegram y envía `/start`. El sistema validará tu identidad consultando la API externa configurada en `EXTERNAL_DATA_API_URL`.

### 2. API Administrativa (Dashboard Backend)
El servidor FastAPI se levanta localmente en: `http://localhost:8000`

> [!IMPORTANT]
> En un entorno de producción o desarrollo integrado, el acceso debe realizarse a través de Kong. Kong gestionará el login mediante cookies y las inyectará como tokens Bearer al backend.

- **Documentación Interactiva (Swagger):** `http://localhost:8000/docs`
- **Endpoints Principales:**
    - `GET /admin/channels`: Listar canales desde la API externa.
    - `POST /admin/send`: Enviar mensajes masivos a canales registrados.
    - `GET /admin/users`: Ver lista blanca de usuarios autorizados.

---

## Solución de Problemas Comunes

1. **Error de Validación en Pydantic:** Si ves un error de `Extra inputs are not permitted` para variables como `channels_file`, asegúrate de que tu `config.py` tenga activado `extra='ignore'` o elimina esas variables obsoletas de tu `.env`.
2. **IA Desactivada:** Si el bot responde un mensaje genérico sobre consultas inteligentes, es normal; la funcionalidad RAG ha sido desactivada temporalmente en esta versión.
3. **Conexión con Kong:** Si el Dashboard no carga datos, verifica que la cookie de sesión de Kong esté presente en el navegador y que el `AuthInterceptor` del frontend tenga `withCredentials: true`.
