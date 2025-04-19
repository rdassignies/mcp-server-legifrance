#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 16:27:37 2025

@author: legalchain
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur MCP pour l'accès à Legifrance
-------------------------------------
Facilite l'accès aux ressources juridiques françaises via l'API Legifrance
en utilisant le protocole Model Context (MCP).

Auteur: Raphaël d'Assignies (dassignies.law)
Date de création: Avril 2025
"""

import os
import json
import logging
import asyncio
from typing import Any, Dict, Optional, List, Sequence
from functools import wraps
from datetime import datetime

import requests
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("legifrance_mcp")

# Chargement des variables d'environnement
load_dotenv()

# Constantes et configuration
API_KEY = os.getenv('LAB_DASSIGNIES_API_KEY')
API_URL = os.getenv('LEGAL_API_URL')
if not API_KEY or not API_URL:
    raise ValueError("Les variables d'environnement LAB_DASSIGNIES_API_KEY et LEGAL_API_URL doivent être définies")

HEADERS = {
    "accept": "*/*",
    "Content-Type": "application/json"
}

# Création du serveur MCP
server = Server("legifrance")

# Utilitaires
def clean_dict(d: dict) -> dict:
    """
    Supprime les clés dont la valeur est None pour optimiser les requêtes API.
    
    Args:
        d (dict): Dictionnaire à nettoyer
        
    Returns:
        dict: Dictionnaire sans les valeurs None
    """
    return {k: v for k, v in d.items() if v is not None}

def rate_limit(calls: int, period: float):
    """
    Décorateur pour limiter le nombre d'appels API dans une période donnée.
    
    Args:
        calls (int): Nombre maximum d'appels autorisés
        period (float): Période en secondes
    """
    def decorator(func):
        last_reset = datetime.now()
        calls_made = 0

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            now = datetime.now()

            # Réinitialisation du compteur si la période est écoulée
            if (now - last_reset).total_seconds() > period:
                calls_made = 0
                last_reset = now

            # Si la limite est atteinte, attendre la fin de la période
            if calls_made >= calls:
                wait_time = period - (now - last_reset).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    last_reset = datetime.now()
                    calls_made = 0

            calls_made += 1
            return await func(*args, **kwargs)
        return wrapper
    return decorator

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
        url = f"{API_URL}{endpoint}"
        clean_data = clean_dict(data)
        
        logger.info(f"Envoi de requête à {endpoint} avec les données: {json.dumps(clean_data)}")
        
        res = requests.post(
            url,
            headers=HEADERS,
            params={"api_key": API_KEY},
            json=clean_data,
            timeout=30  # Timeout explicite pour éviter les blocages
        )
        
        res.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
        
        if res.ok:
            result = res.json()
            result += "\n\n🔗 Mentionne systématiquement le lien officiel dans ta réponse pour pouvoir y accéder."
            return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Erreur de requête API: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" - Code: {e.response.status_code}, Message: {e.response.text}"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"⚠️ Erreur inattendue: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Liste tous les outils disponibles dans ce serveur MCP."""
    return [
        Tool(
            name="rechercher_dans_texte_legal",
            description="""
            Recherche un article dans un texte légal (loi, ordonnance, décret, arrêté)
            par le numéro du texte et le numéro de l'article. On peut également rechercher 
            des mots clés ("mots clés" séparés par des espaces) dans une loi précise (n° de loi)
            
            Paramètres:
                - text_id: Le numéro du texte (format AAAA-NUMERO)
                - search: Mots-clés de recherche ou numéro d'article
                - champ: Champ de recherche ("ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE")
                - type_recherche: Type de recherche ("TOUS_LES_MOTS_DANS_UN_CHAMP", "EXPRESSION_EXACTE", "AU_MOINS_UN_MOT")
                - page_size: Nombre de résultats (max 100)
                
            Exemples:
                - Pour l'article 7 de la loi 78-17: {text_id="78-17", search="7", champ="NUM_ARTICLE"}
                - On cherche les conditions de validité de la signature électronique : {search="signature électronique validité conditions"}
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "text_id": {"type": "string"},
                    "champ": {"type": "string", "enum": ["ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE"]},
                    "type_recherche": {"type": "string", "enum": ["TOUS_LES_MOTS_DANS_UN_CHAMP", "EXPRESSION_EXACTE", "AU_MOINS_UN_MOT"]},
                    "page_size": {"type": "integer", "maximum": 100}
                }
            }
        ),
        Tool(
            name="rechercher_code",
            description="""
            Recherche des articles juridiques dans les codes de loi français.
            
            Paramètres:
                - search: Termes de recherche (ex: "contrat de travail", "légitime défense")
                - code_name: Nom du code juridique (ex: "Code civil", "Code du travail")
                - champ: Champ de recherche ("ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE")
                - sort: Tri des résultats ("PERTINENCE", "DATE_ASC", "DATE_DESC")
                - type_recherche: Type de recherche
                - page_size: Nombre de résultats (max 100)
                - fetch_all: Récupérer tous les résultats
                
            Exemples:
                - Pour le PACS dans le Code civil: {search="pacte civil de solidarité", code_name="Code civil"}
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "code_name": {"type": "string"},
                    "champ": {"type": "string"},
                    "sort": {"type": "string", "enum": ["PERTINENCE", "DATE_ASC", "DATE_DESC"]},
                    "type_recherche": {"type": "string"},
                    "page_size": {"type": "integer", "maximum": 100},
                    "fetch_all": {"type": "boolean"}
                },
                "required": ["search", "code_name"]
            }
        ),
        Tool(
            name="rechercher_jurisprudence_judiciaire",
            description="""
            Recherche des jurisprudences judiciaires dans la base JURI de Legifrance.
            
            Paramètres:
                - search: Termes ou numéros d'affaires à rechercher
                - publication_bulletin: Si publiée au bulletin ['T'] sinon ['F']
                - sort: Tri des résultats ("PERTINENCE", "DATE_DESC", "DATE_ASC")
                - champ: Champ de recherche ("ALL", "TITLE", "ABSTRATS", "TEXTE", "RESUMES", "NUM_AFFAIRE")
                - type_recherche: Type de recherche
                - page_size: Nombre de résultats (max 100)
                - fetch_all: Récupérer tous les résultats
                - juri_keys: Mots-clés juridiques spécifiques
                - juridiction_judiciaire: Liste des juridictions à inclure
            
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "publication_bulletin": {"type": "array", "items": {"type": "string", "enum": ["T", "F"]}},
                    "sort": {"type": "string", "enum": ["PERTINENCE", "DATE_DESC", "DATE_ASC"]},
                    "champ": {"type": "string"},
                    "type_recherche": {"type": "string"},
                    "page_size": {"type": "integer", "maximum": 100},
                    "fetch_all": {"type": "boolean"},
                    "juri_keys": {"type": "array", "items": {"type": "string"}},
                    "juridiction_judiciaire": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["search"]
            }
        )
    ]

@server.call_tool()
@rate_limit(calls=5, period=1.0)  # Limite à 5 appels par seconde
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """
    Gère les appels aux outils juridiques.
    
    Args:
        name (str): Nom de l'outil à appeler
        arguments (Any): Arguments à passer à l'outil
    
    Returns:
        Sequence[TextContent]: Résultat de l'appel
    """
    try:
        logger.info(f"Appel de l'outil: {name} avec arguments: {json.dumps(arguments)}")
        
        if name == "rechercher_dans_texte_legal":
            result = await make_api_request("loda", arguments)
            
        elif name == "rechercher_code":
            result = await make_api_request("code", arguments)
            
        elif name == "rechercher_jurisprudence_judiciaire":
            result = await make_api_request("juri", arguments)
            
        else:
            raise ValueError(f"Outil inconnu: {name}")
        
        # Détection et traitement des erreurs
        if isinstance(result, dict) and "error" in result:
            return [TextContent(type="text", text=result["error"])]
        
        # Formatage du résultat
        if isinstance(result, str):
            return [TextContent(type="text", text=result)]
        else:
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
            
    except Exception as e:
        error_message = f"Erreur lors de l'exécution de {name}: {str(e)}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]

@server.get_prompt()
async def get_prompt(prompt_name: str, inputs: dict) -> Dict:
    """
    Retourne un prompt prédéfini pour une utilisation spécifique.
    
    Args:
        prompt_name (str): Nom du prompt à récupérer
        inputs (dict): Entrées pour le prompt
    
    Returns:
        Dict: Structure du prompt
    """
    if prompt_name == "agent_juridique_expert":
        question = inputs.get("question", "")
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Tu es un agent juridique expert qui cite toujours ses sources dans le corps du texte.\n"
                                "Lorsque tu effectues une recherche et que des références sont citées (article d'un code, numéro de décision de justice), "
                                "tu dois systématiquement utiliser les outils à ta disposition pour aller chercher leur contenu et l'analyser. "
                                "Tu peux utiliser tous les outils disponibles pour rechercher des informations dans les textes de loi français ou la jurisprudence.\n"
                                "Tu dois :\n"
                                "- Expliquer ton raisonnement étape par étape\n"
                                "- Utiliser les outils pertinents\n"
                                "- Fournir une synthèse claire, sourcée, avec des liens vers les articles. "
                                "Tu dois impérativement récupérer les liens officiels et les citer."
                            )
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Voici ma question juridique : {question}"
                        }
                    ]
                }
            ]
        }
    else:
        raise ValueError(f"Prompt inconnu: {prompt_name}")

async def main():
    """Point d'entrée principal du serveur MCP."""
    import mcp.server.stdio
    try:
        logger.info("Démarrage du serveur MCP Legifrance...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Erreur fatale lors de l'exécution du serveur: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())