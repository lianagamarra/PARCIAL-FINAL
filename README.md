# Comments API — Trabajo Final Web II

API REST desarrollada con **FastAPI**, base de datos en **Supabase** e integración con **Hugging Face** para análisis de sentimiento mediante inteligencia artificial.

## Descripción del proyecto

Esta aplicación permite gestionar comentarios de usuarios con operaciones CRUD completas. Al crear o actualizar un comentario, la API analiza automáticamente su sentimiento (positivo, negativo o neutral) usando un modelo de IA externo. También expone un endpoint dedicado para analizar texto sin guardarlo en la base de datos.

## Tecnologías utilizadas

|Tecnología|Uso|
|-|-|
|FastAPI|Framework web y documentación automática|
|Supabase|Base de datos PostgreSQL en la nube|
|Hugging Face Inference API|Análisis de sentimiento con IA|
|Pydantic|Validación de datos|
|Uvicorn|Servidor ASGI|

## Estructura del proyecto

```
project/
├── core/
│   ├── \_\_init\_\_.py
│   └── config.py
├── database/
│   ├── \_\_init\_\_.py
│   └── supabase.py
├── routes/
│   ├── \_\_init\_\_.py
│   └── comments.py
├── schemas/
│   ├── \_\_init\_\_.py
│   └── comment\_schema.py
├── services/
│   ├── \_\_init\_\_.py
│   └── ai\_service.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Requisitos previos

* Python 3.10 o superior
* Cuenta en [Supabase](https://supabase.com/)
* Cuenta en [Hugging Face](https://huggingface.co/) (opcional, para IA externa)
* Git y cuenta en GitHub

## Configuración paso a paso

### 1\. Clonar el repositorio

```bash
git clone https://github.com/TU\_USUARIO/comments-api.git
cd comments-api
```

### 2\. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3\. Configurar Supabase

1. Crea un proyecto en [Supabase](https://supabase.com/dashboard).
2. Ve a **SQL Editor** y ejecuta:

```sql
CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    sentiment TEXT,
    created\_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir acceso anon en desarrollo" ON comments;

CREATE POLICY "Permitir acceso anon en desarrollo"
ON comments
FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);
```

3. Copia la **URL** del proyecto y la clave **publishable** o **anon** desde **Project Settings → API**.

### 4\. Configurar variables de entorno

```bash
copy .env.example .env
```

Edita `.env`:

```env
SUPABASE\_URL=https://tu-proyecto.supabase.co
SUPABASE\_KEY=tu\_clave\_de\_supabase
HUGGINGFACE\_API\_TOKEN=tu\_token\_de\_huggingface
```

> \*\*Nota:\*\* Si no configuras `HUGGINGFACE\_API\_TOKEN`, la API usará un análisis local basado en palabras clave.

### 5\. Ejecutar la aplicación

```bash
uvicorn main:app --reload
```

La API estará disponible en:

* **API:** http://127.0.0.1:8000
* **Swagger UI:** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

## Endpoints

|Método|Endpoint|Descripción|
|-|-|-|
|GET|`/comments`|Listar todos los comentarios|
|GET|`/comments/{id}`|Obtener un comentario por ID|
|POST|`/comments`|Crear un comentario|
|PUT|`/comments/{id}`|Actualizar un comentario|
|DELETE|`/comments/{id}`|Eliminar un comentario|
|POST|`/comments/analyze`|Analizar sentimiento con IA|

## Ejemplos de uso

### Crear comentario

```http
POST /comments
Content-Type: application/json

{
  "author": "Ana",
  "content": "La aplicación funciona muy bien"
}
```

**Response (201):**

```json
{
  "id": 1,
  "author": "Ana",
  "content": "La aplicación funciona muy bien",
  "sentiment": "positivo"
}
```

### Listar comentarios

```http
GET /comments
```

**Response (200):**

```json
\[
  {
    "id": 1,
    "author": "Ana",
    "content": "La aplicación funciona muy bien",
    "sentiment": "positivo"
  }
]
```

### Analizar con IA

```http
POST /comments/analyze
Content-Type: application/json

{
  "content": "El servicio fue lento y no me gustó"
}
```

**Response (200):**

```json
{
  "content": "El servicio fue lento y no me gustó",
  "sentiment": "negativo"
}
```

### Petición inválida

```http
POST /comments
Content-Type: application/json

{
  "author": "",
  "content": ""
}
```

**Response (422):**

```json
{
  "detail": "Los campos author y content son obligatorios"
}
```

\---

## ¿Qué se hizo en el programa?

Esta sección explica, archivo por archivo, qué se implementó dentro del proyecto.

### `main.py`

Es el punto de entrada de la aplicación. Aquí se crea la instancia de `FastAPI`, se define el título, la versión y la descripción que aparecen en la documentación automática. También se implementó un manejador de errores personalizado (`validation\_exception\_handler`) que traduce al español los mensajes de validación que genera Pydantic por defecto (por ejemplo, "Field required" se convierte en "El campo es obligatorio"). Por último, se registra el router de comentarios y se expone un endpoint raíz (`GET /`) que confirma que la API está activa.

### `core/config.py`

Contiene la configuración centralizada de la aplicación. Se encarga de leer las variables de entorno (`SUPABASE\_URL`, `SUPABASE\_KEY`, `HUGGINGFACE\_API\_TOKEN`, `APP\_NAME`, `APP\_VERSION`) usando Pydantic Settings, de modo que el resto del código nunca accede directamente a `os.environ`, sino a un objeto `settings` ya validado.

### `database/supabase.py`

Inicializa el cliente de Supabase usando la URL y la clave definidas en las variables de entorno. Este cliente es el que se reutiliza en las rutas para hacer las operaciones contra la tabla `comments`.

### `schemas/comment\_schema.py`

Define los modelos de datos (Pydantic) que validan la información que entra y sale de la API: el esquema para crear un comentario, el de actualización y el de respuesta. Aquí se establecen las reglas de validación, como que `author` y `content` no pueden estar vacíos.

### `routes/comments.py`

Contiene toda la lógica del CRUD sobre la entidad `comments`:

* **POST `/comments`** crea un comentario nuevo y, antes de guardarlo, llama al servicio de IA para calcular su sentimiento.
* **GET `/comments`** devuelve la lista completa de comentarios almacenados en Supabase.
* **GET `/comments/{id}`** devuelve un comentario específico por su ID.
* **PUT `/comments/{id}`** actualiza un comentario existente y vuelve a calcular el sentimiento si el contenido cambió.
* **DELETE `/comments/{id}`** elimina un comentario.
* **POST `/comments/analyze`** es un endpoint independiente que solo analiza el sentimiento de un texto sin guardarlo en la base de datos.

### `services/ai\_service.py`

Es el módulo que integra la inteligencia artificial. Se conecta a la **Hugging Face Inference API** usando el modelo `cardiffnlp/twitter-roberta-base-sentiment-latest` para clasificar un texto como positivo, negativo o neutral. Si no hay token de Hugging Face configurado, o si la llamada a la API externa falla, el sistema cae automáticamente en un análisis local (`\_analyze\_with\_keywords`) que clasifica el sentimiento contando palabras positivas y negativas predefinidas. Esto garantiza que la API siempre responda, incluso sin conexión al servicio externo.

### `.env` / `.env.example`

Separan la configuración sensible (credenciales de Supabase, token de Hugging Face) del código fuente. El archivo `.env` real no se sube al repositorio (está en `.gitignore`); solo se versiona `.env.example` como plantilla.

\---

## Pruebas documentadas

Realiza cada prueba en Swagger (`/docs`), toma captura de pantalla e inclúyela en este README.

### Prueba válida 1 — Crear comentario

|Campo|Valor|
|-|-|
|Endpoint|`POST /comments`|
|Body|`{"author": "Ana", "content": "La aplicación funciona muy bien"}`|
|Resultado esperado|Status `201`, comentario creado con `sentiment: "positivo"`|

!\[Prueba válida 1](ruta-de-tu-captura-1.png)

### Prueba válida 2 — Listar comentarios

|Campo|Valor|
|-|-|
|Endpoint|`GET /comments`|
|Resultado esperado|Status `200`, arreglo con los comentarios registrados|

!\[Prueba válida 2](ruta-de-tu-captura-2.png)

**Alternativa — Análisis con IA:**

|Campo|Valor|
|-|-|
|Endpoint|`POST /comments/analyze`|
|Body|`{"content": "El servicio fue lento y no me gustó"}`|
|Resultado esperado|Status `200`, `sentiment: "negativo"`|

### Prueba inválida — Campos vacíos

|Campo|Valor|
|-|-|
|Endpoint|`POST /comments`|
|Body|`{"author": "", "content": ""}`|
|Resultado esperado|Status `422`, mensaje de error de validación|

!\[Prueba inválida](ruta-de-tu-captura-3.png)

\---

## Integración con IA

El servicio `services/ai\_service.py` se conecta a la **Hugging Face Inference API** usando el modelo `cardiffnlp/twitter-roberta-base-sentiment-latest`.

1. Se envía el texto del comentario a la API de Hugging Face.
2. El modelo devuelve una etiqueta de sentimiento.
3. La API traduce el resultado a español: `positivo`, `negativo`, `neutral`.
4. Si la API externa no está disponible, se usa un análisis local por palabras clave.

## Video demostrativo

Graba un video corto (2–5 minutos) mostrando:

1. Inicio del servidor con `uvicorn main:app --reload`
2. Prueba de endpoints en Swagger (`/docs`)
3. Verificación de datos en Supabase (opcional)

**Enlace al video: https://www.youtube.com/watch?v=VjpGmn5sM5g** 

## Autor

* **Nombre:** \[Tu nombre]
* **Curso:** Web II
* **Institución:** \[Tu institución]

## Licencia

Proyecto académico — uso educativo.

