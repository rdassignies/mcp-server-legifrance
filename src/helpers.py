import json
from typing import Dict, Sequence

import requests
from mcp.types import TextContent

from src.config import config, logger


def clean_dict(d: dict) -> dict:
    """
    Supprime les clés dont la valeur est None pour optimiser les requêtes API.

    Args:
        d (dict): Dictionnaire à nettoyer

    Returns:
        dict: Dictionnaire sans les valeurs None
    """
    return {k: v for k, v in d.items() if v is not None}


async def make_api_request(endpoint: str, data: Dict) -> Dict:
    """
    Fonction générique pour effectuer des requêtes API avec gestion d'erreurs.

    Args:
        endpoint (str): Point de terminaison de l'API (sans le domaine)
        data (Dict): Données à envoyer dans la requête

    Returns:
        Dict: Résultat de la requête ou message d'erreur
    """
    try:
        url = f"{config.api.url}{endpoint}"
        clean_data = clean_dict(data)

        logger.info(f"Envoi de requête à {endpoint} avec les données: {json.dumps(clean_data)}")

        res = requests.post(
            url,
            headers=config.api.headers,
            params={"api_key": config.api.key},
            json=clean_data,
            timeout=config.api.timeout
        )

        content_type = res.headers.get("Content-Type", "")
        response_body = res.text

        if res.ok:
            try:
                result = res.json()
            except requests.exceptions.JSONDecodeError:
                result = response_body  # fallback sur le texte brut

            if isinstance(result, str):
                result += "\n\n🔗 Mentionne systématiquement et impérativement le lien officiel dans ta réponse pour pouvoir y accéder."
            return result

        if (res.status_code == 422 or res.status_code == 404) and "text/plain" in content_type:
            return {"error": response_body}

        if "application/json" in content_type:
            try:
                return {"error": res.json()}
            except requests.exceptions.JSONDecodeError:
                return {"error": response_body}

        return {"error": f"Erreur {res.status_code} : {response_body}"}

    except requests.exceptions.RequestException as e:
        logger.error("Erreur de connexion à l'API", exc_info=True)
        return {"error": f"Erreur de connexion : {e}"}

    except Exception as e:
        # Uniquement pour les erreurs de connexion ou autres problèmes graves
        logger.error(f"Erreur de connexion: {str(e)}")
        return {"error": f"Erreur de connexion: {str(e)}"}


async def execute_tool(tool_name: str, endpoint: str, arguments: Dict, log_message: str) -> Sequence[TextContent]:
    """
    Fonction commune pour exécuter un outil avec gestion des erreurs et formatage des résultats.

    Args:
        tool_name (str): Nom de l'outil (pour les messages d'erreur)
        endpoint (str): Point de terminaison de l'API
        arguments (Dict): Arguments à envoyer à l'API
        log_message (str): Message à logger

    Returns:
        Sequence[TextContent]: Résultat formaté pour le client MCP
    """
    try:
        logger.info(log_message)

        result = await make_api_request(endpoint, clean_dict(arguments))

        if isinstance(result, dict) and "error" in result:
            return [TextContent(type="text", text=result["error"])]

        if isinstance(result, str):
            return [TextContent(type="text", text=result)]

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        error_message = f"Erreur lors de l'exécution de {tool_name}: {str(e)}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]
