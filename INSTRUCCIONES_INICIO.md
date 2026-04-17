# Manual de Inicio: ¿Cómo Ejecutar el Bot?

Sigue este tutorial paso a paso para levantar correctamente el proyecto desde cero en tu entorno de desarrollo.

## Prerrequisitos

Debes asegurarte de tener en tu equipo:
- Python 3.10 o superior (Idealmente Python 3.12 o 3.14).
- Cuenta de Telegram, y tu propio Bot creado desde `@BotFather` para poseer tu `{TELEGRAM_BOT_TOKEN}`.
- Cuenta de desarrollador de OpenAI para poseer una `{OPENAI_API_KEY}`.

---

## Paso 1: Configurar Variables de Entorno
Crea o edita el archivo llamado `.env` en la raíz del proyecto y asegúrate de cargar tus credenciales del modo siguiente:

```env
TELEGRAM_BOT_TOKEN="tu-token-telegram-aqui"
OPENAI_API_KEY="sk-proj-tu-llave-openai-aqui"
```

## Paso 2: Crear el Archivo de Conocimientos
En la carpeta `/data`, asegúrate de tener ubicado el archivo `interrapidisimo_info.txt` o cualquier archivo de conocimiento que desees que el bot pueda analizar. Si la carpeta no existe, modifícalo directamente, ya que el sistema debe tener al menos un documento para procesar.

## Paso 3: Activar Entorno e Instalar Librerías

Abre una consola o terminal en la ruta principal del proyecto y ejecuta:

**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**En MacOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

*(Nota: Ocasionalmente la instalación de dependencias puede demorar ya que compila librerías científicas e instala un entorno robusto de LlamaIndex).*

## Paso 4: Ejecutar la Aplicación

Para desplegar localmente tu bot (utilizando la tecnología de "Long Polling" para escuchar los mensajes en vivo sin requerir configuración extra de dominios):

```powershell
python main.py
```

### Validando la inicialización:
Verás mensajes en la consola al transcurso de unos segundos informando que:
1. `INFO:root:Iniciando indexador de RAG...` y `HTTP Request: POST api.openai.com/v1/embeddings` informándote que está convirtiendo tu texto local en conocimiento vectorial con IA.
2. `INFO:aiogram.dispatcher:Run polling for bot @tu_bot` avisándote que acaba de enlazarse hacia tu bot en Telegram con éxito y actualmente está encrustado ejecutando.

## Paso 5: Probar
1. Abre Telegram y navega a tu bot. 
2. Escribe `/start` (el panel de Menú de botones debería emerger).
3. Escribe cualquier pregunta libre para probar el RAG o acciona un botón para los flujos pre-fabricados.
