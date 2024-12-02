import re

import soundfile as sf
import speech_recognition as sr
from pydub import AudioSegment
import noisereduce as nr
import librosa


# Конвертация аудио из OGG в WAV
def convert_ogg_to_wav(input_path: str, output_path: str):
    audio = AudioSegment.from_file(input_path, format="ogg")
    audio.export(output_path, format="wav")


# Фильтрация шума
def reduce_noise(input_path: str, output_path: str):
    y, sr_rate = librosa.load(input_path, sr=None)  # Загрузка аудио
    reduced_noise = nr.reduce_noise(y=y, sr=sr_rate)  # Уменьшение шума
    sf.write(output_path, reduced_noise, sr_rate)  # Запись очищенного аудио в файл


# Распознавание текста из аудио
def recognize_speech_from_audio(file_path: str) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="ru-RU")
    except sr.UnknownValueError:
        return "Не удалось распознать текст."
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания: {e}"


# Функция для очистки текста от знаков препинания и приведения к нижнему регистру
def clean_text(text: str) -> str:
    # Удаление всех знаков препинания
    cleaned_text = re.sub(r'[^\w\s]', '', text)
    # Приведение текста к нижнему регистру
    return cleaned_text.lower()


# Функция для объединения всех строк в одну
def merge_lines(text: str) -> str:
    # Заменяем символы новой строки на пробелы
    return ' '.join(text.splitlines())


# Сравнение текста с эталоном
def calculate_similarity(recognized_text: str, original_text: str) -> float:
    from difflib import SequenceMatcher
    return round(SequenceMatcher(None, recognized_text, original_text).ratio() * 100, 2)
