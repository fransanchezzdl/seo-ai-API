# SEO Content API

Proyecto de clase: API REST en **Python ≥ 3.12**, **FastAPI**, **Pydantic 2** y
**OpenAI SDK**, preparada para **Azure OpenAI** con un deployment de **gpt-4o-mini**
o **gpt-4o** compatible con salidas estructuradas. Implementa los cinco endpoints
solicitados, validación de entrada/salida, prompts especializados y errores HTTP.

---

## Evaluación y reconocimiento

<div align="center">

### **Calificación final: 10 / 10**

*Evaluado por **UNIR** (Universidad Internacional de La Rioja)*  
*Programa de Tecnología Aplicada a los Negocios*

</div>

> **Comentario de evaluación:** Aprobado con la máxima puntuación, cumpliendo el 100 % de los criterios técnicos. API bien estructurada mediante routers, modelos Pydantic y servicios, con integración de Azure OpenAI. Destacan la validación de entradas, la generación segura de JSON-LD y la amplia cobertura de pruebas.

---

## Ejecutar

```bash
python3.12 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Edita `.env` localmente (no se sube a Git):

```dotenv
AZURE_OPENAI_API_KEY=tu_clave
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=nombre_exacto_de_tu_deployment
OPENAI_API_VERSION=2024-10-21
```

`AZURE_OPENAI_DEPLOYMENT` es el **nombre que asignaste al despliegue**, que puede
ser distinto del nombre del modelo. En el recurso de Azure, selecciona una versión
que admita Structured Outputs, por ejemplo gpt-4o-mini 2024-07-18 o gpt-4o
2024-08-06. La disponibilidad depende de la suscripción y región. El crédito de
Azure no se aplica a una clave de la API directa de OpenAI.

Opcionalmente, sin variables `AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_API_KEY`, se
admite `OPENAI_API_KEY` y `OPENAI_MODEL`. Azure tiene prioridad y una configuración
parcial de Azure produce un 503, en lugar de usar otro proveedor inadvertidamente.

```bash
uvicorn app.main:app --reload
```

- Swagger interactivo: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Especificación: http://127.0.0.1:8000/openapi.json
- Salud del proceso: `GET /` (no verifica credenciales ni consume crédito).

Sin credenciales, la documentación y las pruebas funcionan; los endpoints de
IA responden 503. Las llamadas reales consumen la cuota del proveedor.

## Endpoints y criterios de evaluación

| Endpoint POST | Implementación y validaciones |
|---|---|
`/api/keywords/generate` | 3–10 semilla, 5–15 long-tail, 3–10 preguntas; clasificación informacional/transaccional de cada término, sin omisiones ni duplicados; idioma e industria en el prompt. |
`/api/articles/generate` | H1 único en `title`, secciones H2/H3 ordenadas, keyword principal en el H1, secundarias presentes, CTAs integrados y densidad calculada. |
`/api/metadata/generate` | 3–5 títulos distintos ≤60 caracteres y 3–5 descripciones distintas ≤160; keyword principal en todas las variantes; contadores calculados. |
`/api/faqs/extract` | FAQs anidadas, 50–150 palabras por respuesta, máximo solicitado entre 1 y 10; JSON-LD FAQPage construido en servidor y consistente con las respuestas. |
`/api/social/summaries` | Twitter/X, LinkedIn, Instagram y Facebook; tonos específicos, hashtags y CTA por red; validación del texto completo; redes no solicitadas en `null`. |

### Ejemplos de peticiones

Hay cinco JSON listos para enviar en `examples/`. Por ejemplo:

```bash
curl -sS http://127.0.0.1:8000/api/keywords/generate \
  -H 'Content-Type: application/json' --data-binary @examples/keywords.json

curl -sS http://127.0.0.1:8000/api/articles/generate \
  -H 'Content-Type: application/json' --data-binary @examples/articles.json

curl -sS http://127.0.0.1:8000/api/metadata/generate \
  -H 'Content-Type: application/json' --data-binary @examples/metadata.json

curl -sS http://127.0.0.1:8000/api/faqs/extract \
  -H 'Content-Type: application/json' --data-binary @examples/faqs.json

curl -sS http://127.0.0.1:8000/api/social/summaries \
  -H 'Content-Type: application/json' --data-binary @examples/social.json
```

El flujo editorial recomendado es keywords → artículo → metadatos/FAQs/redes.
En Swagger puedes copiar los resultados de una etapa como entrada de la siguiente.

### Contratos y decisiones

- **Entradas:** cadenas vacías/solo espacios y campos desconocidos se rechazan.
  `word_count` admite 300–2500; el artículo generado debe quedar en ±20% del objetivo.
  `max_questions` admite 1–10; las plataformas se seleccionan de una lista cerrada.
- **Keywords:** `intent_classification` es una lista de objetos `keyword` + `intent`,
  compatible con esquemas estrictos. Son propuestas de IA; no datos de volumen de búsqueda.
- **Artículo:** cada H3 pertenece al H2 anterior. `sections[].content` contiene
  párrafos, sin repetir encabezados. `call_to_actions` identifica frases que ya
  aparecen en el artículo, por lo que no deben añadirse de nuevo al renderizarlo.
  `keyword_density` = ocurrencias exactas de la frase principal / palabras × 100,
  sin distinguir mayúsculas. Incluye título y secciones; los CTAs no se cuentan
  dos veces. El máximo del 3% es una regla editorial del proyecto, no una regla
  universal de SEO. No se inventa un porcentaje ni se impone una densidad mínima.
- **Metadatos:** `char_count` se recalcula con `len(text)` (incluye espacios y signos).
  Una variante demasiado larga se regenera, sin cortar una palabra, keyword o CTA.
  La keyword de entrada admite hasta 50 caracteres para dejar margen en el título.
- **FAQs:** pueden devolverse menos preguntas si el artículo no permite más.
  `json_ld_schema` es un string JSON listo para un bloque `application/ld+json`;
  se construye desde las FAQs validadas y se escapa `<` al serializarlo. El marcado
  válido no garantiza que un buscador muestre rich snippets.
- **Social:** `text`/`caption` es la publicación completa con hashtags y CTA.
  Los campos `hashtags` y `call_to_action` identifican partes ya incluidas; no hay
  que concatenarlos otra vez. X aplica un presupuesto conservador de 280 unidades
  ponderadas; LinkedIn admite 3000 caracteres, Instagram 2200 y Facebook un máximo
  **editorial** de 2000 para estos resúmenes. Las plataformas no solicitadas son `null`.
- **Calidad:** prompts orientados a intención, utilidad, lenguaje natural y fidelidad
  al texto fuente. La relevancia semántica y el estilo requieren revisión humana;
  las validaciones automáticas garantizan las restricciones medibles.

## Arquitectura

```text
app/
  main.py                 FastAPI, routers y documentación
  config.py               Cliente AzureOpenAI reutilizable y variables .env
  errors.py               Manejo centralizado de errores sin filtrar secretos
  models/                 Modelos públicos y validadores Pydantic
  routers/                Cinco rutas HTTP con response_model
  services/
    seo_service.py        Prompts, SDK, validación contextual y cálculos
    structured.py         Adaptación del JSON Schema a Azure
examples/                 Entradas JSON de los cinco endpoints
tests/                    Pruebas de modelos, HTTP, configuración y SDK
.github/workflows/        Ejecución de pruebas en Python 3.12 y 3.14
```

Los handlers síncronos de FastAPI ejecutan el cliente síncrono en su thread pool.
`chat.completions.parse()` recibe un modelo Pydantic; todos los objetos prohíben
campos adicionales. Azure admite un subconjunto de JSON Schema: se omiten solo
en el esquema enviado los límites no compatibles, **manteniendo los validadores
Pydantic al parsear y los límites públicos de OpenAPI**.

Las respuestas inválidas reciben **un único intento adicional** con el error de
validación como feedback. El SDK tiene timeout de 90 segundos por llamada y un
reintento de transporte; una petición completa puede tardar más de 90 segundos.
No se reintenta editorialmente un rechazo de contenido ni errores de autenticación.

| HTTP | Situación |
|---|---|
| 422 | Entrada inválida o rechazo de contenido por el modelo |
| 429 | Límite de peticiones o cuota del proveedor |
| 502 | Error del proveedor o salida inválida tras la corrección |
| 503 | Falta de configuración, credenciales/permisos incorrectos o fallo de conexión |
| 504 | Timeout del proveedor |

Los errores tienen formato `{"detail": "mensaje"}`; los 422 de validación de entrada
usan el detalle estándar de FastAPI. Los logs registran tipo de error y ruta,
sin claves, prompts ni contenido privado del proveedor.

## Verificación y entrega

```bash
pytest -q
ruff check .
ruff format --check .
```

Las pruebas no necesitan `.env` ni conexión a Azure. Cubren los cinco endpoints,
validaciones, errores HTTP, corrección de respuestas, filtrado de plataformas,
conteos, jerarquía SEO, JSON-LD, configuración Azure y una llamada al **SDK real
con transporte HTTP simulado** para verificar serialización y parsing.

## Referencias

- [OpenAI Docs: Structured Outputs y Pydantic](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).
- [Microsoft: salidas estructuradas y restricciones del esquema Azure](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs).
- [Microsoft: cuotas y límites](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/quotas-limits?tabs=REST).
