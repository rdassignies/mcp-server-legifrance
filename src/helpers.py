"""
Fonctions utilitaires pour les requêtes API et la gestion des défis WAF.

Ce module contient des fonctions pour effectuer des requêtes API vers Legifrance
et gérer les défis JavaScript du WAF Tiger Protect d'o2switch.

La solution implémentée permet de:
1. Utiliser des en-têtes HTTP qui imitent un navigateur web
2. Détecter les défis WAF dans les réponses 503
3. Extraire et analyser le JavaScript pour résoudre le défi
4. Maintenir une session persistante pour réutiliser les cookies
5. Gérer différents types de défis (formulaires, redirections, valeurs JavaScript)

Cette approche évite l'utilisation de dépendances externes comme Playwright,
Puppeteer ou Selenium, tout en permettant de contourner les protections WAF.
"""

import json
import re
import time
import random
import logging
from typing import Dict, Sequence, Tuple, Optional
from urllib.parse import urlparse, parse_qs, urljoin

import requests
from mcp.types import TextContent

from src.config import config, logger

# Session persistante pour réutiliser les cookies entre les requêtes
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


def clean_dict(d: dict) -> dict:
    """
    Supprime les clés dont la valeur est None pour optimiser les requêtes API.

    Args:
        d (dict): Dictionnaire à nettoyer

    Returns:
        dict: Dictionnaire sans les valeurs None
    """
    return {k: v for k, v in d.items() if v is not None}


def get_browser_headers() -> Dict[str, str]:
    """
    Génère des en-têtes HTTP qui imitent un navigateur web moderne.

    Returns:
        Dict[str, str]: En-têtes HTTP simulant un navigateur
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def extract_js_challenge_value(content: str) -> Optional[Dict[str, str]]:
    """
    Extrait et évalue des expressions JavaScript simples du défi WAF.

    Cette fonction recherche des expressions JavaScript qui définissent des valeurs
    ou des cookies nécessaires pour passer le défi WAF.

    Args:
        content (str): Le contenu HTML/JavaScript de la réponse

    Returns:
        Optional[Dict[str, str]]: Dictionnaire des valeurs extraites ou None
    """
    # Chercher des assignations de variables simples
    values = {}

    # Chercher des expressions comme: var challenge = "abc123";
    var_assignments = re.finditer(r'var\s+(\w+)\s*=\s*[\'"]([^\'"]*)[\'"]', content)
    for match in var_assignments:
        name, value = match.groups()
        values[name] = value

    # Chercher des expressions comme: document.cookie = "challenge=abc123; path=/";
    cookie_assignments = re.finditer(r'document\.cookie\s*=\s*[\'"]([^=]+)=([^;]+)', content)
    for match in cookie_assignments:
        name, value = match.groups()
        values[name] = value

    return values if values else None


def handle_waf_challenge(response: requests.Response) -> Tuple[bool, Optional[requests.Response]]:
    """
    Gère les défis JavaScript du WAF Tiger Protect.

    Cette fonction analyse la réponse 503, extrait le défi JavaScript,
    résout le défi et soumet la réponse pour obtenir les cookies nécessaires.

    Args:
        response (requests.Response): La réponse 503 contenant le défi JavaScript

    Returns:
        Tuple[bool, Optional[requests.Response]]: 
            - Un booléen indiquant si le défi a été résolu avec succès
            - La réponse après résolution du défi ou None en cas d'échec
    """
    if response.status_code != 503:
        return False, None

    content = response.text

    # Vérifier si c'est bien un défi WAF
    if "o2switch" not in content and "Tiger Protect" not in content:
        return False, None

    logger.info("Détection d'un défi WAF Tiger Protect. Tentative de résolution...")

    # Extraire les paramètres du défi
    form_action = None
    form_inputs = {}

    # Chercher l'action du formulaire
    form_match = re.search(r'<form.*?action="([^"]*)"', content, re.DOTALL)
    if form_match:
        form_action = form_match.group(1)

    # Chercher tous les champs input
    input_matches = re.finditer(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', content)
    for match in input_matches:
        name, value = match.groups()
        form_inputs[name] = value

    # Extraire des valeurs JavaScript si présentes
    js_values = extract_js_challenge_value(content)
    if js_values:
        logger.info(f"Valeurs JavaScript extraites: {js_values}")
        # Ajouter ces valeurs aux inputs du formulaire si elles correspondent à des noms de champs
        for name, value in js_values.items():
            if name in form_inputs:
                form_inputs[name] = value

    # Si on ne trouve pas de formulaire, chercher une redirection JavaScript
    if not form_action:
        # Chercher différents patterns de redirection
        redirect_patterns = [
            r'window\.location\.href\s*=\s*[\'"]([^\'"]*)[\'"]',
            r'window\.location\s*=\s*[\'"]([^\'"]*)[\'"]',
            r'location\.href\s*=\s*[\'"]([^\'"]*)[\'"]',
            r'setTimeout\(\s*function\s*\(\)\s*{\s*(?:window\.)?location(?:\.href)?\s*=\s*[\'"]([^\'"]*)[\'"]'
        ]

        for pattern in redirect_patterns:
            redirect_match = re.search(pattern, content)
            if redirect_match:
                redirect_url = redirect_match.group(1)
                logger.info(f"Redirection JavaScript détectée vers: {redirect_url}")

                # Ajouter un délai aléatoire pour simuler un comportement humain
                time.sleep(1 + random.random())

                # Mettre à jour les cookies de la session avec ceux extraits du JavaScript
                if js_values:
                    for name, value in js_values.items():
                        _session.cookies.set(name, value)

                # Suivre la redirection avec la session persistante
                redirect_response = _session.get(
                    urljoin(response.url, redirect_url),
                    allow_redirects=True
                )

                return True, redirect_response

    # Si on a trouvé un formulaire, le soumettre
    if form_action and form_inputs:
        logger.info(f"Formulaire de défi détecté. Action: {form_action}, Champs: {list(form_inputs.keys())}")

        # Ajouter un délai aléatoire pour simuler un comportement humain
        time.sleep(1 + random.random())

        # Soumettre le formulaire avec la session persistante
        form_response = _session.post(
            urljoin(response.url, form_action),
            data=form_inputs,
            allow_redirects=True
        )

        return True, form_response

    # Dernière tentative: essayer de faire une requête GET simple avec les cookies
    if js_values:
        logger.info("Tentative de requête GET avec les valeurs JavaScript extraites comme cookies")

        # Mettre à jour les cookies de la session avec ceux extraits du JavaScript
        for name, value in js_values.items():
            _session.cookies.set(name, value)

        time.sleep(1 + random.random())

        # Utiliser la session persistante pour la requête GET
        get_response = _session.get(
            response.url,
            allow_redirects=True
        )

        if get_response.status_code != 503:
            return True, get_response

    logger.warning("Impossible de résoudre le défi WAF: formulaire ou redirection non trouvé")
    return False, None


async def make_api_request(endpoint: str, data: Dict) -> Dict:
    """
    Fonction générique pour effectuer des requêtes API avec gestion d'erreurs.
    Gère également les défis JavaScript du WAF Tiger Protect.

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

        # Fusionner les en-têtes de l'API avec des en-têtes de navigateur
        browser_headers = get_browser_headers()

        # Mettre à jour les en-têtes de la session persistante
        _session.headers.update(browser_headers)
        _session.headers.update(config.api.headers)

        # Effectuer la requête initiale avec la session persistante
        res = _session.post(
            url,
            params={"api_key": config.api.key},
            json=clean_data,
            timeout=config.api.timeout
        )

        # Gérer le défi WAF si nécessaire (code 503)
        if res.status_code == 503:
            challenge_solved, new_response = handle_waf_challenge(res)

            if challenge_solved and new_response:
                logger.info("Défi WAF résolu avec succès. Réessai de la requête originale.")

                # Si le défi a été résolu, les cookies sont déjà dans la session persistante
                # Réessayer la requête originale
                res = _session.post(
                    url,
                    params={"api_key": config.api.key},
                    json=clean_data,
                    timeout=config.api.timeout
                )

                # Journaliser les cookies pour le débogage
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Cookies après résolution du défi: {dict(_session.cookies)}")
            else:
                logger.warning("Impossible de résoudre le défi WAF. Poursuite avec la réponse 503.")

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

        if res.status_code == 503:
            return {"error": f"Erreur 503 Service Unavailable. Possible défi WAF non résolu: {response_body[:200]}..."}

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
