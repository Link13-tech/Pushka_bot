import os
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
    text = re.sub(r'(?<=\w)-(?=\w)', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Функция для объединения всех строк в одну
def merge_lines(text: str) -> str:
    return ' '.join(text.splitlines())


# Функция для вычисления схожести слов с учетом Levenshtein Distance
def are_words_similar(word1: str, word2: str) -> bool:
    # Проверяем замену окончаний "ие" на "ье" и наоборот
    if (word1.endswith("ие") and word2.endswith("ье") and word1[:-2] == word2[:-2]) or \
            (word1.endswith("ье") and word2.endswith("ие") and word1[:-2] == word2[:-2]):
        return True

    # Проверяем замену окончаний "ия" на "ье" и наоборот для слов "наслаждения" и "наслажденье"
    if (word1.endswith("ия") and word2.endswith("ье") and word1[:-2] == word2[:-2]) or \
            (word1.endswith("ье") and word2.endswith("ия") and word1[:-2] == word2[:-2]):
        return True

    # Проверяем расстояние Левенштейна для остальных случаев
    distance = Levenshtein.distance(word1, word2)
    if distance <= 1:
        return True

    return False


# Сравнение текста с эталоном с использованием Jaccard Similarity с учетом схожести слов
def jaccard_similarity_with_fuzzy(recognized_text: str, original_text: str) -> float:
    recognized_text = clean_text(recognized_text)
    original_text = clean_text(original_text)

    print(f"Распознанный текст после очистки: {recognized_text}")
    print(f"Оригинальный текст после очистки: {original_text}")

    recognized_words = recognized_text.split()
    original_words = original_text.split()

    intersection = 0
    for word1 in recognized_words:
        for word2 in original_words:
            if are_words_similar(word1, word2):
                intersection += 1
                original_words.remove(word2)
                break

    union = len(recognized_words) + len(original_words)

    # Вычисление процента совпадения
    similarity = (intersection / union) * 100
    return round(similarity, 2)


# Разбиение аудио на 40-секундные фрагменты с перекрытием и удалением дубликатов на стыке фрагментов
def split_audio(input_path: str, segment_length_ms: int = 39000, overlap_ms: int = 2000, min_segment_length_ms: int = 2000):
    audio = AudioSegment.from_wav(input_path)
    duration_ms = len(audio)

    if duration_ms > segment_length_ms:
        print(f"Длительность аудио больше 39 секунд ({duration_ms / 1000} секунд). Разбиваем на фрагменты.")
        segments = []
        for i in range(0, duration_ms, segment_length_ms - overlap_ms):
            segment = audio[i:i + segment_length_ms]

            if len(segment) < min_segment_length_ms:
                continue

            segment_path = f"audio/segment_{i // (segment_length_ms - overlap_ms)}.wav"
            segment.export(segment_path, format="wav")
            segments.append(segment_path)

        return segments
    else:
        print(f"Длительность аудио меньше или равна 39 секундам ({duration_ms / 1000} секунд).")
        return [input_path]


# Функция для удаления дубликатов на стыке фрагментов (перекрытие)
def remove_overlap_duplicates(segments: list) -> str:
    merged_text = ""
    seen_words = set()
    previous_segment_text = []

    for i, segment_path in enumerate(segments):
        with open(segment_path, 'r') as segment:
            words = segment.read().split()

        if i > 0:
            current_segment_text = words[:2]
            previous_segment_text = previous_segment_text[-2:]

            # Проверка на дублирование первых 2 слов с предыдущим сегментом
            if current_segment_text == previous_segment_text:
                words = words[2:]

        filtered_words = [word for word in words if word not in seen_words]

        merged_text += " ".join(filtered_words) + " "
        seen_words.update(filtered_words)

        previous_segment_text = words

        os.remove(segment_path)

    return merged_text.strip()
