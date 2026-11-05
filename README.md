# Jarvis

Assistant vocal personnel en Python. Tu lui parles dans le micro, Jarvis transcrit ta voix en temps réel (**ElevenLabs Scribe**), réfléchit avec **Google Gemini**, puis te répond à voix haute (**ElevenLabs Text-to-Speech**). Tous les échanges sont archivés dans une base **SQLite**, et une mémoire par résumés automatiques permet à Jarvis de se souvenir de la conversation sur la durée.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration des clés API](#configuration-des-clés-api)
- [Intégration d'ElevenLabs](#intégration-delevenlabs)
- [Base de données SQLite](#base-de-données-sqlite)
- [Utilisation](#utilisation)
- [Fonctionnement détaillé](#fonctionnement-détaillé)
- [Personnalisation](#personnalisation)
- [Dépannage](#dépannage)
- [Limites connues](#limites-connues)
- [Sécurité](#sécurité)

## Fonctionnalités

- Reconnaissance vocale en temps réel via ElevenLabs (`scribe_v2_realtime`) avec détection automatique de fin de phrase (VAD)
- Synthèse vocale naturelle et multilingue via ElevenLabs (`eleven_multilingual_v2`)
- Réponses générées par Gemini (API `google-genai`, Interactions)
- Mémoire à long terme : les anciens échanges sont condensés en résumé par un second appel à Gemini
- Continuité de conversation grâce au `previous_interaction_id` de Gemini
- Historique complet de la conversation stocké dans SQLite
- Configuration persistante (utilisateur, résumé, dernier ID d'interaction) dans un fichier JSON
- Chaque module est exécutable seul pour être testé (`python gemini.py`, `python speech.py`, `python database.py`)

## Architecture

```
   Micro
     │  audio PCM 16 kHz
     ▼
┌──────────────┐   texte    ┌──────────────┐
│  speech.py   │──────────▶ │   main.py    │
│ ElevenLabs   │            │ (orchestre)  │
│ STT  /  TTS  │◀────────── │              │
└──────────────┘  réponse   └──┬───┬───┬───┘
     │ audio                   │   │   │
     ▼                         │   │   │
 Haut-parleurs                 │   │   └────▶ config.py   → database/config.json
                               │   └────────▶ database.py → database/database.db (SQLite)
                               ▼
                         ┌──────────────┐
                         │  gemini.py   │
                         │ réponses +   │
                         │ résumés      │
                         └──────────────┘
```

## Structure du projet

```
Jarvis/
├── main.py            # Boucle principale : écoute → Gemini → voix
├── gemini.py          # Classe Gemini : réponses et résumés de conversation
├── speech.py          # Classe Speech : STT et TTS via ElevenLabs
├── config.py          # Classe Config : configuration persistante (JSON)
├── database.py        # Classe Database : historique des messages (SQLite)
├── database/          # Données locales (créé par toi, ignoré par Git)
│   ├── database.db    # Base SQLite
│   └── config.json    # Configuration persistante (créée automatiquement)
├── requirements.txt   # Dépendances Python
├── .env.example       # Modèle de fichier d'environnement
├── .env               # Tes vraies clés (jamais versionné)
└── README.md
```

## Prérequis

- Python 3.10 ou plus récent
- Un microphone et des haut-parleurs (ou un casque)
- Une clé API **Google Gemini** : [Google AI Studio](https://aistudio.google.com/apikey)
- Une clé API **ElevenLabs** : [elevenlabs.io](https://elevenlabs.io) (Profil → API Keys)
- Les bibliothèques système audio (voir ci-dessous)

### Bibliothèques système

Le projet utilise `sounddevice` (PortAudio) pour le micro et les haut-parleurs, et `soundfile` (libsndfile) pour décoder l'audio renvoyé par ElevenLabs.

**Debian / Ubuntu :**

```bash
sudo apt update
sudo apt install -y python3-venv libportaudio2 libsndfile1 sqlite3
```

`sqlite3` n'est ici que l'outil en ligne de commande, pratique pour inspecter la base. Le module Python `sqlite3` est déjà inclus dans Python.

**macOS (Homebrew) :**

```bash
brew install portaudio libsndfile sqlite
```

**Windows :** PortAudio et libsndfile sont déjà embarqués dans les paquets pip `sounddevice` et `soundfile`, rien à installer en plus.

## Installation

### 1. Récupérer le projet

```bash
git clone https://github.com/<ton-utilisateur>/Jarvis.git
cd Jarvis
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
```

### 3. Installer les dépendances Python avec `requirements.txt`

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Le fichier `requirements.txt` regroupe tous les modules nécessaires :

| Module | Rôle |
|---|---|
| `python-dotenv` | Lecture des clés API depuis le fichier `.env` |
| `google-genai` | Client officiel de l'API Gemini |
| `elevenlabs` | Client officiel ElevenLabs (STT temps réel et TTS) |
| `sounddevice` | Capture du micro et lecture audio |
| `soundfile` | Décodage de l'audio renvoyé par ElevenLabs |
| `numpy` | Dépendance de `sounddevice` / `soundfile` |
| `websockets` | Connexion temps réel à l'API de transcription |

Pour vérifier l'installation :

```bash
pip list | grep -Ei "dotenv|genai|elevenlabs|sounddevice|soundfile"
```

### 4. Préparer le dossier de données

```bash
mkdir -p database
```

Ce dossier contiendra la base SQLite et le fichier de configuration. Il est ignoré par Git.

### 5. Créer la base SQLite

Voir la section [Base de données SQLite](#base-de-données-sqlite).

### 6. Configurer les clés API

```bash
cp .env.example .env
```

Puis édite `.env` (voir la section suivante).

## Configuration des clés API

Le fichier `.env` à la racine du projet contient **deux** clés :

```
GEMINI_API_KEY=ta_cle_gemini
AUDIO_API_KEY=ta_cle_elevenlabs
```

| Variable | Utilisée par | Service |
|---|---|---|
| `GEMINI_API_KEY` | `gemini.py` | Google Gemini |
| `AUDIO_API_KEY` | `speech.py` | ElevenLabs (transcription et voix) |

Attention : la clé ElevenLabs s'appelle bien `AUDIO_API_KEY` dans ce projet, pas `ELEVENLABS_API_KEY`.

Les clés sont lues avec `dotenv.get_key(Path('.env'), ...)`, donc **lance toujours le programme depuis la racine du projet**, là où se trouve `.env`.

## Intégration d'ElevenLabs

Toute la partie audio est gérée par la classe `Speech` dans `speech.py`, qui utilise le SDK officiel `elevenlabs`.

### Créer et configurer ta clé

1. Crée un compte sur [elevenlabs.io](https://elevenlabs.io).
2. Va dans ton profil, rubrique **API Keys**, et crée une clé.
3. Si tu restreins les permissions de la clé, autorise au minimum **Text to Speech** et **Speech to Text**.
4. Copie la clé dans `.env` sous le nom `AUDIO_API_KEY`.

Les appels ElevenLabs consomment des crédits selon ton offre : la synthèse vocale facture les caractères générés, la transcription facture la durée d'audio. Surveille ton quota si tu testes beaucoup.

### Transcription (Speech-to-Text temps réel)

Méthode `Speech.listen()` :

- Le micro est capturé avec `sounddevice.RawInputStream` en PCM 16 bits, mono, **16 000 Hz**, par blocs de 1600 échantillons (100 ms).
- Chaque bloc est encodé en base64 puis envoyé par WebSocket à ElevenLabs.
- Le modèle utilisé est `scribe_v2_realtime`, avec la stratégie de validation `CommitStrategy.VAD` : ElevenLabs détecte lui-même la fin de ta phrase et renvoie la transcription finale.
- Pendant que tu parles, les transcriptions partielles s'affichent dans le terminal (`Vous dite ...`).
- Quand la transcription finale arrive (événement `COMMITTED_TRANSCRIPT`), l'écoute s'arrête et le texte est retourné à `main.py`.
- Une nouvelle connexion est ouverte à chaque tour de parole, puis fermée.

### Synthèse vocale (Text-to-Speech)

Méthode `Speech.say(text)` :

- Le texte de la réponse est envoyé à `client.text_to_speech.convert(...)` avec le modèle `eleven_multilingual_v2` (qui gère très bien le français).
- L'audio est reçu en flux, assemblé en bytes, décodé avec `soundfile`, puis joué avec `sounddevice`.
- Les appels bloquants s'exécutent dans `asyncio.to_thread` pour ne pas figer la boucle asynchrone.

### Paramètres modifiables dans `Speech.__init__`

| Attribut | Valeur par défaut | Description |
|---|---|---|
| `sample_rate` | `16000` | Fréquence d'échantillonnage du micro (doit rester cohérente avec `AudioFormat.PCM_16000`) |
| `transcript_model_id` | `scribe_v2_realtime` | Modèle de transcription |
| `voice_model_id` | `eleven_multilingual_v2` | Modèle de synthèse vocale |
| `voice_id` | `JBFqnCBsd6RMkjVDRZzb` | Identifiant de la voix utilisée |

Pour changer de voix, choisis-en une dans la bibliothèque de voix ElevenLabs, copie son **Voice ID** et remplace la valeur de `voice_id`.

### Tester l'audio seul

```bash
python speech.py
```

Parle dans le micro : Jarvis répète « Vous avez dit ... » à voix haute. C'est le meilleur moyen de valider ton micro, tes haut-parleurs et ta clé ElevenLabs avant de lancer l'assistant complet.

## Base de données SQLite

L'historique de chaque conversation est stocké dans une base **SQLite**, via le module `sqlite3` de la bibliothèque standard Python. Aucune installation pip n'est nécessaire et aucun serveur n'est requis : la base est un simple fichier, `database/database.db`.

### Créer la table `messages`

`database.py` ouvre la base (et crée le fichier s'il n'existe pas) mais **ne crée pas la table**. Il faut donc la créer une fois avant le premier lancement.

**Avec le CLI `sqlite3` :**

```bash
sqlite3 database/database.db "CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);"
```

**Ou avec Python :**

```bash
python -c "import sqlite3; c = sqlite3.connect('database/database.db'); c.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'); c.commit(); c.close()"
```

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER | Identifiant auto-incrémenté |
| `role` | TEXT | `user` (ta voix) ou `model` (réponse de Jarvis) |
| `content` | TEXT | Texte du message |
| `created_at` | TEXT | Date d'insertion, remplie automatiquement |

### La classe `Database`

| Méthode | Description |
|---|---|
| `build()` | Ouvre la connexion SQLite si elle n'existe pas encore, et active `sqlite3.Row` pour accéder aux colonnes par nom |
| `save_message(role, msg)` | Enregistre un message dans la table `messages` |
| `execute(request, params)` | Exécute une requête d'écriture avec commit automatique (rollback en cas d'erreur SQLite) |
| `fetchall(request, params)` | Exécute une requête de lecture et retourne toutes les lignes |

### Console SQL interactive

```bash
python database.py
```

```
database > /fetch SELECT * FROM messages ORDER BY id DESC LIMIT 5
database > DELETE FROM messages
database > /exit
```

- `/fetch <requête>` : lecture, affiche les lignes sous forme de dictionnaires
- toute autre commande : écriture avec commit
- `/exit` : quitter

### Consulter l'historique directement

```bash
sqlite3 -header -column database/database.db "SELECT id, role, content FROM messages ORDER BY id DESC LIMIT 10;"
```

### Réinitialiser la mémoire de Jarvis

Pour repartir de zéro, supprime l'historique et la configuration :

```bash
rm database/database.db database/config.json
```

Puis recrée la table (voir plus haut).

## Utilisation

Depuis la racine du projet, avec l'environnement virtuel activé :

```bash
python main.py
```

Jarvis écoute en continu : parle naturellement, fais une pause, il répond à voix haute, puis se remet à l'écoute. Pour arrêter, utilise `Ctrl+C`.

> `main.py` quitte aussi si le texte transcrit contient `/exit`, mais cette chaîne est peu susceptible d'être produite par la reconnaissance vocale. `Ctrl+C` reste la méthode fiable.

Modules testables séparément :

```bash
python gemini.py     # Discussion texte avec Gemini, sans voix ni base
python speech.py     # Test micro + haut-parleurs ElevenLabs
python database.py   # Console SQL sur la base SQLite
```

## Fonctionnement détaillé

Boucle de `main.py` à chaque tour :

1. `Speech.listen()` capture la voix et renvoie le texte transcrit.
2. Le message de l'utilisateur est enregistré dans SQLite (`role = user`).
3. Si l'historique en mémoire dépasse `conversation_limit` messages (4 par défaut), `Gemini.summarize()` condense les plus anciens et les fusionne avec le résumé existant. Le résumé est sauvegardé dans `config.json`.
4. `Gemini.ask()` envoie la requête avec le résumé comme contexte et le dernier `interaction_id`, ce qui permet à Gemini de garder le fil.
5. La réponse est enregistrée dans SQLite (`role = model`), l'`interaction_id` est sauvegardé dans `config.json`.
6. La réponse est affichée dans le terminal puis lue à voix haute via `Speech.say()`.

### Deux niveaux de mémoire

- **Court terme** : le `previous_interaction_id` de Gemini conserve le contexte immédiat côté serveur.
- **Long terme** : le résumé glissant (`summary`), réinjecté dans les instructions système, conserve les faits importants, préférences, objectifs et tâches en cours de l'utilisateur.

### Fichier `database/config.json`

Créé automatiquement, il contient :

```json
{
  "user": "Bambara Dev",
  "last_interaction_id": "…",
  "summary": "…"
}
```

La classe `Config` utilise des propriétés Python : chaque modification de `user`, `summary` ou `last_interaction_id` est sauvegardée instantanément sur disque.

## Personnalisation

| Ce que tu veux changer | Où |
|---|---|
| Ton prénom / nom d'utilisateur | `user_name` dans `main.py` |
| Nom de l'assistant | paramètre `ainame` de `Gemini` (`gemini.py`) |
| Personnalité et règles de réponse | `self.identity` dans `gemini.py` |
| Fréquence des résumés | `conversation_limit` dans `main.py` |
| Modèle de réponse Gemini | paramètre `model` de `Gemini.ask()` |
| Modèle de résumé Gemini | paramètre `model` de `Gemini.summarize()` |
| Voix, modèle TTS/STT | attributs de `Speech.__init__` dans `speech.py` |
| Emplacement de la base ou de la config | paramètre `path` de `Database` et `Config` |

Les réponses sont demandées en texte brut, sans markdown, afin que la synthèse vocale ne lise pas d'astérisques ou de symboles.

## Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| `OSError: PortAudio library not found` | PortAudio absent | `sudo apt install libportaudio2` |
| `sf.LibsndfileError` / erreur de décodage audio | libsndfile absent ou trop ancien (le MP3 demande libsndfile 1.1+) | `sudo apt install libsndfile1` puis `pip install --upgrade soundfile` |
| Aucun son en sortie | Mauvais périphérique audio par défaut | `python -c "import sounddevice as sd; print(sd.query_devices())"` puis régler le périphérique par défaut du système |
| Le micro ne capte rien | Mauvais périphérique d'entrée ou permission refusée | Même commande que ci-dessus, vérifier les permissions du micro |
| Erreur d'authentification ElevenLabs (401) | `AUDIO_API_KEY` absente, fausse ou sans permissions STT/TTS | Vérifier `.env` et les permissions de la clé |
| Erreur Gemini d'authentification | `GEMINI_API_KEY` absente ou invalide | Vérifier `.env`, lancer depuis la racine du projet |
| `sqlite3.OperationalError: unable to open database file` | Le dossier `database/` n'existe pas | `mkdir -p database` |
| `no such table: messages` | La table n'a pas été créée | Voir [Créer la table messages](#créer-la-table-messages) |
| `ModuleNotFoundError` | Environnement virtuel non activé ou dépendances non installées | `source .venv/bin/activate && pip install -r requirements.txt` |

## Limites connues

- Les réponses sont lues en entier une fois générées (pas de streaming audio), ce qui ajoute une latence.
- Une nouvelle connexion WebSocket de transcription est ouverte à chaque tour.
- Pendant que Jarvis parle, il n'écoute pas : on ne peut pas l'interrompre.
- L'historique SQLite est archivé mais n'est pas relu au démarrage : seul le résumé de `config.json` assure la mémoire entre deux sessions.

## Sécurité

- Ne publie **jamais** ton fichier `.env` : il contient tes clés Gemini et ElevenLabs. Il est exclu par `.gitignore`, seul `.env.example` (sans valeurs réelles) est versionné.
- Si une clé a été exposée par erreur, révoque-la immédiatement (Google AI Studio / ElevenLabs) et génères-en une nouvelle.
- Le dossier `database/` contient tes conversations privées : il est lui aussi ignoré par Git.

## Licence

Full Open Source