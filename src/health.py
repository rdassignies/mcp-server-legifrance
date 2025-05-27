import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.config import logger

# Create a filter to exclude /ping endpoint from logging
class ExcludePingFilter(logging.Filter):
    """
    A logging filter that excludes log messages related to the /ping endpoint.

    This filter is used to prevent the health check endpoint from cluttering
    application logs, as recommended in the FastAPI documentation:
    https://fastapi.tiangolo.com/advanced/middleware/
    """
    def filter(self, record):
        # Check if the log record contains information about the /ping endpoint
        return "/ping" not in getattr(record, "message", "")

# Function to register the ping endpoint with the server
def register_ping_endpoint(server):
    """
    Register the ping endpoint with the server and apply the logging filter.
    
    Args:
        server: The FastMCP server instance
    """
    # Apply the filter to the logger to exclude /ping endpoint logs
    logger.addFilter(ExcludePingFilter())
    
    @server.custom_route("/ping", methods=["GET"])
    async def ping(request: Request) -> JSONResponse:
        """
        Simple health check endpoint that returns a 200 OK response.
        
        This endpoint is excluded from logging using a custom logging filter
        to prevent cluttering application logs with health check requests.
        
        For more information on filtering logs in Python, see:
        https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
        
        Returns:
            JSONResponse: A JSON response with status "ok"
        """
        return JSONResponse({"status": "ok"})
    
    return ping