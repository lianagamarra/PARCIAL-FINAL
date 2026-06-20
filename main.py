import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.config import settings
from routes.comments import router as comments_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API REST para gestionar comentarios con almacenamiento en Supabase "
        "y análisis de sentimiento mediante inteligencia artificial."
    ),
    openapi_tags=[
        {
            "name": "Comentarios",
            "description": "Crear, consultar, actualizar, eliminar y analizar comentarios.",
        },
        {
            "name": "Estado",
            "description": "Verificar que la API esté funcionando correctamente.",
        },
    ],
)


def _traducir_mensaje_validacion(mensaje: str) -> str:
    traducciones = {
        "Field required": "El campo es obligatorio",
        "Input should be a valid integer": "Debe ser un número entero válido",
        "Input should be a valid string": "Debe ser un texto válido",
    }

    if mensaje in traducciones:
        return traducciones[mensaje]

    if mensaje.startswith("Value error, "):
        return mensaje.replace("Value error, ", "", 1)

    match_min = re.match(
        r"String should have at least (\d+) character(s?)", mensaje
    )
    if match_min:
        minimo = match_min.group(1)
        return f"Debe tener al menos {minimo} carácter(es)"

    match_max = re.match(
        r"String should have at most (\d+) character(s?)", mensaje
    )
    if match_max:
        maximo = match_max.group(1)
        return f"No puede superar {maximo} carácter(es)"

    return mensaje


def _traducir_ubicacion(ubicacion: list) -> str:
    partes = []
    for item in ubicacion:
        if item == "body":
            partes.append("cuerpo")
        elif item == "query":
            partes.append("consulta")
        elif item == "path":
            partes.append("ruta")
        elif isinstance(item, str):
            partes.append(item)
        else:
            partes.append(str(item))
    return " / ".join(partes)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errores = []
    mensaje_simple = None

    for error in exc.errors():
        mensaje = _traducir_mensaje_validacion(str(error.get("msg", "")))
        campo = _traducir_ubicacion(error.get("loc", []))

        if error.get("type") == "value_error":
            mensaje_simple = mensaje
            break

        errores.append(
            {
                "campo": campo,
                "tipo": error.get("type"),
                "mensaje": mensaje,
            }
        )

    if mensaje_simple:
        return JSONResponse(status_code=422, content={"detail": mensaje_simple})

    if len(errores) == 1:
        return JSONResponse(status_code=422, content={"detail": errores[0]["mensaje"]})

    return JSONResponse(status_code=422, content={"detail": errores})


@app.get(
    "/",
    tags=["Estado"],
    summary="Estado de la API",
    description="Devuelve un mensaje de confirmación y la versión actual de la aplicación.",
)
def root():
    return {
        "mensaje": "La API de comentarios funciona correctamente",
        "documentacion": "/docs",
        "version": settings.app_version,
    }


app.include_router(comments_router)
