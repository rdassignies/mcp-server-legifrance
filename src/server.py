import asyncio
from typing import Dict, List, Sequence
from tenacity import retry

from fastmcp.server import FastMCP
from mcp.types import TextContent
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.helpers import execute_tool
from src.config import config, logger

server = FastMCP(
    name=config.mcp.name,
    instructions=config.mcp.instructions
)

@server.custom_route("/ping", methods=["GET"])
async def ping(request: Request) -> JSONResponse:
    """
    Simple health check endpoint that returns a 200 OK response.

    Returns:
        JSONResponse: A JSON response with status "ok"
    """
    return JSONResponse({"status": "ok"})


@server.tool(
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
    """
)
@retry(wait=config.retry.wait, stop=config.retry.stop)
async def rechercher_dans_texte_legal(
    search: str = None,
    text_id: str = None,
    champ: str = None,
    type_recherche: str = None,
    page_size: int = None
) -> Sequence[TextContent]:
    """
    Recherche un article dans un texte légal.

    Args:
        search: Mots-clés de recherche ou numéro d'article
        text_id: Le numéro du texte (format AAAA-NUMERO)
        champ: Champ de recherche
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max 100)

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    arguments = {
        "search": search,
        "text_id": text_id,
        "champ": champ,
        "type_recherche": type_recherche,
        "page_size": page_size
    }

    log_message = f"Recherche dans texte légal avec: {search}, {text_id}"

    return await execute_tool(
        "rechercher_dans_texte_legal",
        config.endpoints.rechercher_dans_texte_legal,
        arguments,
        log_message
    )

@server.tool(
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
    """
)
@retry(wait=config.retry.wait, stop=config.retry.stop)
async def rechercher_code(
    search: str,
    code_name: str,
    champ: str = None,
    sort: str = None,
    type_recherche: str = None,
    page_size: int = None,
    fetch_all: bool = None
) -> Sequence[TextContent]:
    """
    Recherche des articles juridiques dans les codes de loi français.

    Args:
        search: Termes de recherche
        code_name: Nom du code juridique
        champ: Champ de recherche
        sort: Tri des résultats
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max 100)
        fetch_all: Récupérer tous les résultats

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    arguments = {
        "search": search,
        "code_name": code_name,
        "champ": champ,
        "sort": sort,
        "type_recherche": type_recherche,
        "page_size": page_size,
        "fetch_all": fetch_all
    }

    log_message = f"Recherche dans code: {search}, {code_name}"

    return await execute_tool(
        "rechercher_code",
        config.endpoints.rechercher_code,
        arguments,
        log_message
    )

@server.tool(
    name="rechercher_jurisprudence_judiciaire",
    description="""
    Recherche des jurisprudences judiciaires dans la base JURI de Legifrance.

    Paramètres:
        - search: Termes ou numéros d'affaires à rechercher
        - publication_bulletin: Si publiée au bulletin ['T'] sinon ['F']
        - sort: Tri des résultats ("PERTINENCE", "DATE_DESC", "DATE_ASC")
        - champ: Champ de recherche ("ALL", "TITLE", "ABSTRATS", "TEXTE", "RESUMES", "NUM_AFFAIRE")
        - type_recherche: Type de recherche
        - page_size: Nombre de résultats (max. 100)
        - fetch_all: Récupérer tous les résultats
        - juri_keys: Mots-clés pour extraire des champs comme 'titre'. Par défaut, le titre, le texte et les résumés sont extraits
        - juridiction_judiciaire: Liste des juridictions à inclure parmi ['Cour de cassation', 'Juridictions d'appel', ]

    Exemples : 
        - Obtenir un panorama de la jurisprudence par mots clés : 
            search = "tierce opposition salarié société liquidation", page_size=100, juri_keys=['titre']
        - Obtenir toutes les jurisprudences sur la signature électronique : 
            search = "signature électronique", fetch_all=True, juri_keys=['titre', 'sommaire']
        - Obtenir les 20 dernières jurisprudences sur la signature électronique des juridictions d'appel
         search = "signature électronique", page_size, sort='DATE_DESC', juridiction_judiciaire=['Juridictions d'appel']]
    """
)
@retry(wait=config.retry.wait, stop=config.retry.stop)
async def rechercher_jurisprudence_judiciaire(
    search: str,
    publication_bulletin: List[str] = None,
    sort: str = None,
    champ: str = None,
    type_recherche: str = None,
    page_size: int = None,
    fetch_all: bool = None,
    juri_keys: List[str] = None,
    juridiction_judiciaire: List[str] = None
) -> Sequence[TextContent]:
    """
    Recherche des jurisprudences judiciaires dans la base JURI de Legifrance.

    Args:
        search: Termes ou numéros d'affaires à rechercher
        publication_bulletin: Si publiée au bulletin ['T'] sinon ['F']
        sort: Tri des résultats
        champ: Champ de recherche
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max. 100)
        fetch_all: Récupérer tous les résultats
        juri_keys: Mots-clés pour extraire des champs
        juridiction_judiciaire: Liste des juridictions à inclure

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    arguments = {
        "search": search,
        "publication_bulletin": publication_bulletin,
        "sort": sort,
        "champ": champ,
        "type_recherche": type_recherche,
        "page_size": page_size,
        "fetch_all": fetch_all,
        "juri_keys": juri_keys,
        "juridiction_judiciaire": juridiction_judiciaire
    }

    log_message = f"Recherche de jurisprudence: {search}"

    return await execute_tool(
        "rechercher_jurisprudence_judiciaire",
        config.endpoints.rechercher_jurisprudence_judiciaire,
        arguments,
        log_message
    )

@server.prompt(name="agent_juridique_expert", description="Utilise un agent juridique expert pour répondre à des questions de droit français")
async def agent_juridique_expert(question: str):
    """
    Prompt pour l'agent juridique expert.

    Args:
        question (str): La question juridique

    Returns:
        Dict: Structure du prompt
    """
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

async def main():
    """Point d'entrée principal du serveur MCP."""
    try:
        logger.info(f"Démarrage du serveur MCP Legifrance avec transport {config.mcp.transport}...")

        transport_kwargs = {}
        if config.mcp.transport in ["streamable-http", "sse"]:
            transport_kwargs["host"] = config.mcp.host
            transport_kwargs["port"] = config.mcp.port
            transport_kwargs["path"] = config.mcp.path

        await server.run_async(
            transport=config.mcp.transport,
            **transport_kwargs
        )
    except Exception as e:
        logger.error(f"Erreur fatale lors de l'exécution du serveur: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
