"""FastAPI app: API REST de generacion de contenido SEO con IA."""

from fastapi import FastAPI

from app.errors import install_error_handlers
from app.routers import articles, faqs, keywords, metadata, social

app = FastAPI(
    title="SEO Content API",
    description=(
        "API REST de generacion de contenido SEO con IA: keywords, articulos, "
        "metadatos, FAQs con JSON-LD y resumenes para redes sociales."
    ),
    version="1.0.0",
)

install_error_handlers(app)

app.include_router(keywords.router)
app.include_router(articles.router)
app.include_router(metadata.router)
app.include_router(faqs.router)
app.include_router(social.router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok", "docs": "/docs"}
