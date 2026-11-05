import asyncio

from gemini import Gemini
from config import Config
from database import Database
from speech import Speech




async def main():
    user_name = 'Bambara Dev'
    conversation_limit = 4

    speech = Speech()
    database = Database()
    gemini = Gemini(user_name)
    config = Config()
    config.user = user_name

    while True:
        # cmd = input('/exit pour quitter\n > ').strip()
        cmd = await speech.listen()

        if '/exit' in cmd:
            break

        if not cmd:
            continue

        database.save_message('user', cmd)

        # Summarize
        if len(gemini.conversation) > conversation_limit:
            config.summary = gemini.summarize(conversation_limit, config.summary)
            
        # Ask Gemini
        response = gemini.ask(cmd, summary=config.summary, last_conversation_id=config.last_interaction_id)

        database.save_message('model', response['content'])

        config.last_interaction_id = response['interaction_id']

        print(response['content'])
        await speech.say(response['content'])



if __name__ == '__main__':
    asyncio.run(main())