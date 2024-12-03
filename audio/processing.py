import os
import re
from dotenv import load_dotenv
import soundfile as sf
from pydub import AudioSegment
import librosa
import noisereduce as nr
from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType

load_dotenv()

# Конфигурация API-ключа Yandex SpeechKit
configure_credentials(
    yandex_credentials=creds.YandexCredentials(
        api_key=os.getenv("YANDEX_API_KEY")
    )
)


# Конвертация аудио из OGG в WAV
def convert_ogg_to_wav(input_path: str, output_path: str):
    audio = AudioSegment.from_file(input_path, format="ogg")
    audio.export(output_path, format="wav")


# Фильтрация шума
def reduce_noise(input_path: str, output_path: str):
    y, sr_rate = librosa.load(input_path, sr=None)
    reduced_noise = nr.reduce_noise(y=y, sr=sr_rate)
    sf.write(output_path, reduced_noise, sr_rate)


# Изменение частоты дискретизации
def change_sample_rate(input_path: str, output_path: str, target_sr: int):
    y, sr = librosa.load(input_path, sr=None)
    y_resampled = librosa.resample(y, sr, target_sr)
    sf.write(output_path, y_resampled, target_sr)


# Подготовка аудио для распознавания (снижение шума и изменение частоты дискретизации)
def prepare_audio(input_path: str, output_path: str, target_sr: int):
    reduce_noise(input_path, output_path)
    change_sample_rate(output_path, output_path, target_sr)


# Распознавание текста из аудио
def recognize_speech_from_audio(file_path: str) -> str:
    model = model_repository.recognition_model()

    model.model = 'general'
    model.language = 'ru-RU'
    model.audio_processing_type = AudioProcessingType.Full

    try:
        result = model.transcribe_file(file_path)
        transcript = result[0].raw_text
        return transcript.strip()
    except Exception as e:
        return f"Ошибка при распознавании речи: {e}"


# Очистка текста
def clean_text(text: str) -> str:
    cleaned_text = re.sub(r'[^\w\s]', '', text)
    return cleaned_text.lower()


# Объединение всех строк текста
def merge_lines(text: str) -> str:
    return ' '.join(text.splitlines())


# Сравнение текста с эталоном
def calculate_similarity(recognized_text: str, original_text: str) -> float:
    from difflib import SequenceMatcher
    return round(SequenceMatcher(None, recognized_text, original_text).ratio() * 100, 2)
