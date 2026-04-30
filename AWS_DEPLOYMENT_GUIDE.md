# Guía de Despliegue en AWS ECS

Esta guía contiene los comandos necesarios para preparar y desplegar el bot en AWS.

## 1. Subir Imagen a Amazon ECR

```bash
# 1. Autenticar Docker con AWS
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

# 2. Crear el repositorio (solo la primera vez)
aws ecr create-repository --repository-name bot-telegram

# 3. Construir la imagen
docker build -t bot-telegram .

# 4. Etiquetar la imagen
docker tag bot-telegram:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/bot-telegram:latest

# 5. Subir la imagen
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/bot-telegram:latest
```

## 2. Configuración en la Consola de AWS (Puntos Clave)

### ECS Task Definition
- **Compatibilidad**: FARGATE.
- **Memoria/CPU**: 0.5 GB / 0.25 vCPU es suficiente para este bot.
- **Variables de Entorno**: Configura `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `WEBHOOK_URL`, etc., o usa **Secrets Manager**.

### Load Balancer (ALB)
- **Protocolo**: HTTPS (Puerto 443).
- **Certificado**: Selecciona el certificado de ACM para tu dominio.
- **Health Check**: Configura el path `/` (puerto 8000) y espera un status 200.

### Seguridad (Security Groups)
- **ALB SG**: Permitir entrada 443 desde `0.0.0.0/0`.
- **ECS SG**: Permitir entrada 8000 solo desde el SG del ALB.

## 3. Actualizar Servicio ECS

Si ya tienes el servicio corriendo y solo subiste una nueva imagen:

```bash
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment
```
