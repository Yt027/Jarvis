import dotenv
from pathlib import Path
import asyncio
import queue
import io
import soundfile as sf
import base64 as b64
import sounddevice as sd

from elevenlabs import (
    ElevenLabs,
    RealtimeEvents,
    RealtimeAudioOptions,
    CommitStrategy,
    AudioFormat
)


class Speech:
    def __init__(self):
        self.api_key = dotenv.get_key(Path('.env'), 'AUDIO_API_KEY')
        self.client = ElevenLabs(api_key = self.api_key)
        self.sample_rate = 16000
        self.transcript_model_id = 'scribe_v2_realtime'
        self.voice_model_id = 'eleven_multilingual_v2'
        self.voice_id = 'JBFqnCBsd6RMkjVDRZzb'
        self.speech_to_text = ''
        self.audio_queue = queue.Queue()
        self.connection = None
        self.committed = asyncio.Event()
        self.loop = None

    async def say(self, text):
        audio = await asyncio.to_thread(
            self.generate_audio,
            text
        )

        audio_data, sample_rate = sf.read(
            file=io.BytesIO(audio),
            dtype='float32'
        )

        sd.play(
            data=audio_data,
            samplerate=sample_rate
        )

        await asyncio.to_thread(sd.wait)

    def generate_audio(self, text):
        generated_audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id=self.voice_model_id,
            text=text
        )

        return b''.join(generated_audio)

    async def connect(self):
        self.loop = asyncio.get_running_loop()

        self.connection = await self.client.speech_to_text.realtime.connect(RealtimeAudioOptions(
            model_id=self.transcript_model_id,
            sample_rate=self.sample_rate,
            audio_format=AudioFormat.PCM_16000,
            commit_strategy=CommitStrategy.VAD
        ))


        def on_partial(data):
            text = data.get('text', '')
            print('Vous dite ' + text)

        def on_commit(data):
            text = data.get('text', '')
            print('Transcription finale: ' + text)
            self.speech_to_text = text
            self.loop.call_soon_threadsafe(self.committed.set)

        def on_error(error):
            print('Oops il y a eu une erreur de transcription, ' + str(error))

        self.connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, on_partial)
        self.connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, on_commit)
        self.connection.on(RealtimeEvents.ERROR, on_error)

    async def listen(self):
        self.speech_to_text = ''
        self.committed.clear()

        await self.connect()

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                dtype='int16',
                blocksize=1600,
                channels=1,
                callback=self.audio_callback
            ):
                while not self.committed.is_set():
                    chunk = await asyncio.to_thread(self.audio_queue.get)
                    encoded = b64.b64encode(chunk).decode('ascii')

                    await self.connection.send({
                        'audio_base_64': encoded,
                        'sample_rate': self.sample_rate
                    })
                return self.speech_to_text
        finally:
            await self.connection.close()

    def audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))


async def local_run():
    speech = Speech()
    cmd = await speech.listen()
    response = 'Vous avez dit ' + cmd
    print(cmd)
    await speech.say(response)



if __name__ == '__main__':
    asyncio.run(local_run())