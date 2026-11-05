import dotenv
from pathlib import Path
from google import genai


class Gemini:
    def __init__(self, username, ainame='Jarvis'):
        self.user = username
        self.sys = ainame
        self.conversation = []

        self.api_key = dotenv.get_key(Path('.env'), 'GEMINI_API_KEY')
        self.client = genai.Client(api_key=self.api_key)

        self.identity = f"""
            Tu es {self.sys}, l'assistant personnel de {self.user}.

            Ton rôle est d'aider l'utilisateur, de répondre à ses questions
            et de tenir une conversation naturelle.

            Règles :
            - Réponds directement à la demande.
            - Ne fournis pas de résumé de la conversation sauf si l'utilisateur le demande.
            - Ne décris pas ton processus de réflexion.
            - Donne uniquement la réponse utile à l'utilisateur.
            - Tes réponses doivent toujours être formattée en format brute, pas de markdown ici.
            """

    def summarize(self, limit, current_summary='', model='gemini-3.5-flash-lite'):
        print('> Nouveau résumé en cours')
        history = self.conversation[:limit]

        transcript = '\n'.join(
            f"{self.user if message['role'] == 'user' else self.sys} a dit {message['content']}" for message in history
        )

        summarizer_identity = f'''
            Tu es le module de mémoire de {self.sys}, dont le rôle est défini ainsi :
            {self.identity}

            Ta tâche est de mettre à jour le résumé d'une conversation.

            Consignes :
            - Conserve les faits importants et les préférences communiqués par {self.user}.
            - Conserve ses objectifs, décisions et tâches en cours.
            - Fusionne le résumé existant avec les nouveaux échanges.
            - Évite les répétitions et les informations inutiles.
            - N'invente aucune information.
            - Retourne uniquement le résumé actualisé, sans commentaire.
        '''

        prompt = f'''
        Résumé acutel:
        {current_summary}

        Nouvelles conversation à résumer:
        {transcript}
        '''

        interaction = self.client.interactions.create(
            model=model,
            input=prompt,
            system_instruction=summarizer_identity
        )

        self.conversation = self.conversation[limit:]

        return interaction.output_text
        
    def ask(self, prompt, model='gemini-flash-lite-latest', summary='', last_conversation_id=None):
        instructions = f'''
        Tu es {self.sys}:
        {self.identity}

        Voici le résumé des dernière conversation:
        {summary}
        '''
        interaction = self.client.interactions.create(
            model=model,
            input=prompt,
            system_instruction=instructions,
            previous_interaction_id=last_conversation_id
        )

        response = interaction.output_text

        self.conversation.append({
            'role': 'user',
            'content': prompt
        })

        self.conversation.append({
            'role': 'model',
            'content': response
        })

        return {
            'content': response,
            'interaction_id': interaction.id
        }



if __name__ == '__main__':
    gemini = Gemini('Bambara Dev')
    while True:
        cmd = input('/exit pour quitter\n Gemini > ').strip()

        if '/exit' in cmd:
            break

        response = gemini.ask(cmd)
        print(response)