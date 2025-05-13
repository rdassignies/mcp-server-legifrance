# mcp-server-legifrance

Serveur MCP [Model Context Protocol](https://modelcontextprotocol.io/introduction) expérimental permettant d'interroger les bases juridiques françaises via l'API Legifrance dans des LLMs compatibles comme Claude.

## Description

Ce projet implémente un serveur MCP qui permet d'accéder aux ressources juridiques françaises (textes légaux, codes, jurisprudence) directement depuis un Large Language Model. Il facilite les recherches juridiques en rendant les données de Legifrance accessibles via des outils interactifs.

Il faut suite à la création du package [pylegifrance](https://github.com/rdassignies/pylegifrance). 

### Qu'est-ce que le MCP ?

Le Model Context Protocol (MCP) est un protocole standardisé développé par Anthropic qui permet aux modèles de langage comme Claude d'interagir de manière structurée avec des outils et services externes. Il s'agit d'une avancée intéressante dans l'interopérabilité des LLMs car il établit un cadre commun pour l'échange de données et l'exécution de fonctions entre les modèles et les API tierces. Jusqu'à maintenant, il fallait développer, pour chaque service, des appels de fonctions spécifiques. 

### L'interopérabilité via MCP

L'importance du MCP réside dans sa capacité à créer une interface standardisée entre les LLMs et les systèmes externes. Cette standardisation présente plusieurs avantages :

1. **Architecture modulaire** : Les développeurs peuvent créer des outils spécialisés qui sont facilement intégrables à différents LLMs compatibles avec le protocole.

2. **Sécurité accrue** : Le MCP limite l'accès des modèles aux seules fonctionnalités explicitement définies, réduisant ainsi les risques de sécurité.

3. **Maintenance simplifiée** : Les mises à jour des outils externes peuvent être faites indépendamment du modèle, facilitant l'évolution des systèmes.

4. **Extension des capacités** : Les LLMs peuvent accéder à des données en temps réel et exécuter des opérations complexes qu'ils ne pourraient pas réaliser seuls.

### mcp-server-legifrance ? 

L’idée est d’exploiter la puissance des modèles de langage comme Claude pour effectuer des traitements sur des contenus juridiques officiels via Légifrance, et à terme, d’autres bases de données publiques comme le RNE, le BODACC, etc. Les premiers résultats sont très prometteurs et permettent de pallier certaines limites de la recherche statistique classique proposée par Légifrance. Le service est en amélioration continue, mais vous pouvez déjà consulter quelques exemples de recherches ci-dessous.

Le serveur prend en charge les fonctionnalités suivantes:
- Recherche dans les textes légaux (lois, ordonnances, décrets, arrêtés)
- Consultation des articles de codes juridiques français
- Recherche dans la jurisprudence judiciaire

Les autres fonds Legifrance seront bientôt implémentés. 

Si vous souhaitez accéder directement à l'API Legifrance pour connecter votre propre serveur MCP, 
c'est par ici : [https://lab.dassignies.law](https://lab.dassignies.law/api/docs) ou [linkedin](https://fr.linkedin.com/in/dassignies)

## Prérequis

- Python 3.9+
- Clé API pour Legifrance (à obtenir auprès de [lab.dassignies.law](https://lab.dassignies.fr/))
- Un modèle compatible avec le protocole MCP (comme Claude desktop)

## Installation

3. Créez un environnement virtuel et activez-le:
```bash
python -m venv venv 
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```
```bash
uv venv .venv 
source .venv/bin/activate  # Sur Windows: venv\Scripts\activate
```
2. Installer via pip:
```bash
pip install git+https://github.com/rdassignies/mcp-server-legifrance.git
```

3. Installer via uv
```bash
uv pip install git+https://github.com/rdassignies/mcp-server-legifrance.git
```


4. Créez un fichier `.env` à la racine du projet avec vos identifiants:
```
LAB_DASSIGNIES_API_KEY=votre_clé_api
LEGAL_API_URL=https://lab.dassignies.law/api/ # ou l'URL correspondante
```

## Utilisation


### Intégration avec Claude

C'est l'intégration la plus "simple". 


1. Utilisez le fichier de configuration suivant pour intégrer le serveur MCP dans Claude Desktop. 
Pour trouver ce fichier, il faut aller dans paramètres>Développeur>modifier la configuration (renvoie vers le fichier de configuration au format .json). 

Il existe également une procédure à la ligne de commande via uv qui sera documentée ultérieurement. 

Voici un exemple d'utilisation:

```python
{
  "mcpServers": {
    "legifrance": {
      "command": "<CHEMIN_VERS_VOTRE_REP>/mcp-server-legifrance/venv/bin/python",
            "args": [
                "<CHEMIN_VERS_VOTRE_REP>/mcp-server-legifrance/src/server.py"
		]

    }
  }
}
```
2. Démarrer Claude desktop, vous devez voir apparaître des icônes outils : 
![alt text](image.png)

## Outils disponibles

### 1. rechercher_dans_texte_legal

Recherche des articles dans les textes légaux (lois, ordonnances, décrets, arrêtés).

**Paramètres:**
- **text_id**: Identifiant du texte (ex: "78-17" pour la loi informatique et libertés)
- **search**: Mots-clés ou numéro d'article
- **champ**: Zone de recherche ("ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE")
- **type_recherche**: Mode de recherche ("TOUS_LES_MOTS_DANS_UN_CHAMP", "EXPRESSION_EXACTE", "AU_MOINS_UN_MOT")
- **page_size**: Nombre de résultats (max 100)

Pour les détails, cf [https://lab.dassignies.law/api/docs](https://lab.dassignies.law/api/docs)

**Exemple:**
Pour rechercher l'article 7 de la loi 78-17:
```
{
  "text_id": "78-17",
  "search": "7",
  "champ": "NUM_ARTICLE"
}
```

### 2. rechercher_code

Recherche des articles dans les codes juridiques français.

Par ex. "Rédige moi une synthèse sur le régime juridique du PACS"

<img width="793" alt="image" src="https://github.com/user-attachments/assets/9af3dd26-cef1-4859-b4b4-55bcfaeb0d4f" />


**Paramètres:**
- **search**: Termes de recherche
- **code_name**: Nom du code (ex: "Code civil", "Code du travail")
- **champ**: Zone de recherche
- **sort**: Tri des résultats
- **type_recherche**: Mode de recherche
- **page_size**: Nombre de résultats
- **fetch_all**: Si tous les résultats doivent être récupérés

**Exemple:**
Pour rechercher des informations sur le PACS dans le Code civil, le modèle de langage va envoyer la requête suivante : 
```
{
  "search": "pacte civil de solidarité",
  "code_name": "Code civil"
}
```
Pour les détails, cf [https://lab.dassignies.law/api/docs](https://lab.dassignies.law/api/docs)

### 3. rechercher_jurisprudence_judiciaire

Recherche dans la base de jurisprudence judiciaire. On peut utiliser la puissance des modèles de langage pour faire des recherches de jurisprudences directement dans Legifrance. 

**Exemple 1** Panorama des dernières jp sur un thème particulier (ex. "Trouve moi les dernières jp sur la rupture brutale des relations commerciales établies et rédige moi un tableau de synthèse" ). 

<img width="1456" alt="image" src="https://github.com/user-attachments/assets/e5d77948-7ddf-434c-be31-24feacbfbb22" />

**Exemple 2** A partir d'une décision particulière connu (numéro de pourvoi 23-23.382), on peut faire des analyses par étapes : 
1. On trouve l'arrêt et Claude génère la fiche d'arrêt
2. On lui demande d'extraire les articles visés et de les trouver dans Legifrance
3. On lui demande de trouver des jp similaires
4. etc ...


![image](https://github.com/user-attachments/assets/306724b7-5a42-41c2-9b96-ac591d8880b9)


**Paramètres:**
- **search**: Termes ou numéro d'affaire
- **publication_bulletin**: Si publiée au bulletin ["T"] ou non ["F"]
- **sort**: Tri des résultats
- **champ**: Zone de recherche
- **type_recherche**: Mode de recherche
- **page_size**: Nombre de résultats
- **fetch_all**: Si tous les résultats doivent être récupérés
- **juri_keys**: Champs de réponse à extraire 
- **juridiction_judiciaire**: Liste des juridictions

Pour les détails, cf [https://lab.dassignies.law/api/docs](https://lab.dassignies.law/api/docs)

## Prompts prédéfinis

Le serveur peut inclure des prompts prédéfinis pour faciliter l'utilisation. 
Pour le moment, seul un prompt a été implémenté à titre d'exemple. Il est possible de mettre en place des prompts beaucoup plus 
détaillés notamment pour effectuer des opérations de type *deepsearch* ou des extractions dans plusieurs documents ... 

### agent_juridique_expert

Crée un agent juridique expert qui:
- Cite systématiquement ses sources
- Utilise les outils pertinents pour rechercher des informations
- Fournit des analyses étape par étape
- Inclut les liens officiels vers les textes juridiques

**Usage:**
```python
# Exemple d'utilisation du prompt prédéfini
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[
        {
            "role": "user", 
            "content": [
                {
                    "type": "tool_use",
                    "id": "prompt_use_1",
                    "name": "legifrance.get_prompt",
                    "input": {
                        "prompt_name": "agent_juridique_expert",
                        "inputs": {
                            "question": "Quelles sont les conditions de validité d'un contrat de mariage?"
                        }
                    }
                }
            ]
        }
    ]
)
```

## Limitations

- Les requêtes sont limitées à 10 par seconde pour respecter les limites de l'API
- Une connexion internet est nécessaire pour accéder aux bases juridiques
- Le serveur ne met pas en cache les résultats, chaque requête interroge l'API

## Contribution

Les contributions sont les bienvenues! Veuillez ouvrir une issue ou soumettre une pull request pour toute amélioration ou correction.

## Licence

[MIT License](LICENSE)
