import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.config import logger


class ExcludePingFilter(logging.Filter):
    """Filtre qui exclut les logs contenant /ping."""

    def filter(self, record):
        return "/ping" not in str(record.getMessage())


def register_ping_endpoint(server):
    """Enregistre le point de terminaison ping avec le serveur et applique le filtre de journalisation.

    Args:
        server: L'instance du serveur FastMCP.
    """
    # Applique le filtre au logger pour exclure les logs du point de terminaison /ping
    logger.addFilter(ExcludePingFilter())

    # Applique également le filtre au logger uvicorn pour supprimer les logs HTTP
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(ExcludePingFilter())

    @server.custom_route("/ping", methods=["GET"])
    async def ping(request: Request) -> JSONResponse:
        """Point de terminaison simple de vérification d'état qui retourne une réponse 200 OK.

        Ce point de terminaison est exclu de la journalisation en utilisant un filtre
        personnalisé pour éviter d'encombrer les journaux d'application avec les requêtes
        de vérification d'état.

        Returns:
            Une réponse JSON avec le statut "ok".

        Reference:
            https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
        """
        return JSONResponse({"status": "ok"})

    return ping
