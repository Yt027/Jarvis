# Jarvis

Assistant vocal personnel propulsé par l'API Gemini de Google. Jarvis écoute ta voix, répond avec Gemini, lit la réponse à voix haute, et garde une mémoire des échanges grâce à un système de résumé automatique.

## Fonctionnalités

- Conversation vocale : écoute (speech-to-text) et réponse parlée (text-to-speech)
- Réponses générées par Gemini via l'API `google-genai` (Interactions)
- Mémoire à long terme : les anciens échanges sont résumés automatiquement par un second appel à Gemini
- Continuité de conversation grâce à `previous_interaction_id`
- Historique complet des messages stocké dans SQLite
- Configuration persistante (utilisateur, résumé, dernier ID d'interaction) dans un fichier JSON

## Structure du projet

```
Jarvis/
├── main.py          # Boucle principale : écoute -> Gemini -> voix
├── gemini.py        # Classe Gemini : réponses et résumés de conversation
├── speech.py        # Classe Speech : écoute et synthèse vocale
├── config.py        # Classe Config : configuration persistante (JSON)
├── database.py      # Classe Database : historique des messages (SQLite)
├── database/        # Données locales (config.json, database.db)
├── .env.example     # Modèle de fichier d'environnement
└── README.md
```

## Prérequis

- Python 3.10 ou plus récent
- Une clé API Gemini ([Google AI Studio](https://aistudio.google.com/apikey))
- Un microphone et des haut-parleurs

## Installation

```bash
git clone https://github.com/<ton-utilisateur>/Jarvis.git
cd Jarvis

python -m venv .venv
source .venv/bin/activate

pip install python-dotenv google-genai
# + les dépendances utilisées par speech.py (reconnaissance et synthèse vocales)
```

Crée ensuite ton fichier d'environnement à partir du modèle :

```bash
cp .env.example .env
```

Puis renseigne ta clé dans `.env` :

```
GEMINI_API_KEY=ta_cle_api_ici
```

Enfin, assure-toi que le dossier de données existe :

```bash
mkdir -p database
```

La base SQLite doit contenir une table `messages` :

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL
);
```

## Utilisation

```bash
python main.py
```

Parle à Jarvis, il te répondra à voix haute. Dis (ou tape) `/exit` pour quitter.

Chaque module peut aussi être testé séparément :

```bash
python gemini.py     # Chat texte avec Gemini
python database.py   # Console SQL (/fetch <requête> pour lire)
```

## Fonctionnement

1. `Speech.listen()` transforme la voix en texte.
2. Le message est enregistré dans la base SQLite.
3. Si la conversation dépasse `conversation_limit` messages (4 par défaut), les plus anciens sont résumés par Gemini et fusionnés avec le résumé existant.
4. `Gemini.ask()` envoie la requête avec le résumé comme contexte et le dernier `interaction_id` pour la continuité.
5. La réponse est sauvegardée, affichée, puis lue à voix haute.

## Configuration

| Élément | Où | Description |
|---|---|---|
| `GEMINI_API_KEY` | `.env` | Clé API Gemini |
| `user_name` | `main.py` | Nom de l'utilisateur utilisé dans les prompts |
| `conversation_limit` | `main.py` | Nombre de messages avant résumé |
| `ainame` | `gemini.py` | Nom de l'assistant (`Jarvis` par défaut) |
| Modèles | `gemini.py` | Modèle de réponse et modèle de résumé |

Le fichier `database/config.json` est créé automatiquement et stocke `user`, `last_interaction_id` et `summary`.

## Sécurité

Ne publie jamais ton fichier `.env`. Il est ignoré par Git via `.gitignore` ; seul `.env.example` (sans clé réelle) est versionné.

## Licence

Full Open Source