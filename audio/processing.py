import re
import Levenshtein
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
    y, sr_rate = librosa.load(input_path, sr=16000, mono=True)
    reduced_noise = nr.reduce_noise(y=y, sr=sr_rate)
    sf.write(output_path, reduced_noise, sr_rate)


# Распознавание текста из аудио
def recognize_speech_from_audio(file_path: str) -> str:
    recognizer = sr.Recognizer()

    segments = split_audio(file_path)

    recognized_text = ""

    # Обрабатываем каждый сегмент
    for segment_path in segments:
        with sr.AudioFile(segment_path) as source:
            audio = recognizer.record(source)
        try:
            segment_text = recognizer.recognize_google(audio, language="ru-RU")
            recognized_text += " " + segment_text
        except sr.UnknownValueError:
            recognized_text += " [Не удалось распознать текст] "
        except sr.RequestError as e:
            recognized_text += f" [Ошибка сервиса распознавания: {e}] "

    return recognized_text


# Функция для очистки текста от знаков препинания, приведения к нижнему регистру, замены ё на е и удаления лишних пробелов
def clean_text(text: str) -> str:
    text = text.replace('ё', 'е').replace('Ё', 'Е')
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Функция для объединения всех строк в одну
def merge_lines(text: str) -> str:
    return ' '.join(text.splitlines())


# Функция для вычисления схожести слов с учетом Levenshtein Distance
def are_words_similar(word1: str, word2: str) -> bool:
    return Levenshtein.distance(word1, word2) <= 1


# Сравнение текста с эталоном с использованием Jaccard Similarity с учетом схожести слов
def jaccard_similarity_with_fuzzy(recognized_text: str, original_text: str) -> float:
    recognized_text = clean_text(recognized_text)
    original_text = clean_text(original_text)

    print(f"Распознанный текст после очистки: {recognized_text}")
    print(f"Оригинальный текст после очистки: {original_text}")

    recognized_words = recognized_text.split()
    original_words = original_text.split()

    # Нахождение пересечения двух множеств слов с учетом схожести по Левенштейну
    intersection = 0
    for word1 in recognized_words:
        for word2 in original_words:
            if are_words_similar(word1, word2):
                intersection += 1
                original_words.remove(word2)
                break

    # Объединение всех слов (не только пересечение)
    union = len(recognized_words) + len(original_words)

    # Вычисление процента совпадения
    similarity = (intersection / union) * 100
    return round(similarity, 2)


# Разбиение аудио на 1-минутные фрагменты
def split_audio(input_path: str, segment_length_ms: int = 60000):
    audio = AudioSegment.from_wav(input_path)
    duration_ms = len(audio)

    # Проверка, если длительность больше 1 минуты (60 секунд = 60000 миллисекунд)
    if duration_ms > 60000:
        print(f"Длительность аудио больше 1 минуты ({duration_ms / 1000} секунд). Разбиваем на фрагменты.")
        segments = []
        for i in range(0, duration_ms, segment_length_ms):
            segment = audio[i:i + segment_length_ms]
            segment_path = f"audio/segment_{i // segment_length_ms}.wav"
            segment.export(segment_path, format="wav")
            segments.append(segment_path)
        return segments
    else:
        print(f"Длительность аудио меньше или равна 1 минуте ({duration_ms / 1000} секунд).")
        return [input_path]  # Возвращаем оригинальный файл, если его длительность меньше 1 минуты
