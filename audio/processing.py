import os
import re
from difflib import SequenceMatcher

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


# Разбиение аудио на 35-секундные фрагменты с перекрытием и удалением дубликатов на стыке фрагментов
def split_audio(input_path: str, segment_length_ms: int = 35000, overlap_ms: int = 5000):
    audio = AudioSegment.from_wav(input_path)
    duration_ms = len(audio)

    if duration_ms > segment_length_ms:
        print(f"Длительность аудио больше 35 секунд ({duration_ms / 1000} секунд). Разбиваем на фрагменты.")
        segments = []
        for i in range(0, duration_ms, segment_length_ms - overlap_ms):
            segment = audio[i:i + segment_length_ms]
            segment_path = f"audio/segment_{i // (segment_length_ms - overlap_ms)}.wav"
            segment.export(segment_path, format="wav")
            segments.append(segment_path)

        return segments
    else:
        print(f"Длительность аудио меньше или равна 35 секундам ({duration_ms / 1000} секунд).")
        return [input_path]


# Распознавание текста из аудио
def recognize_speech_from_audio(file_path: str) -> str:
    recognizer = sr.Recognizer()

    segments = split_audio(file_path)

    recognized_text = ""
    previous_segment_text = []

    # Обрабатываем каждый сегмент
    for i, segment_path in enumerate(segments):
        with sr.AudioFile(segment_path) as source:
            audio = recognizer.record(source)

        try:
            segment_text = recognizer.recognize_google(audio, language="ru-RU")
        except sr.UnknownValueError:
            segment_text = " [Не удалось распознать текст] "
        except sr.RequestError as e:
            segment_text = f" [Ошибка сервиса распознавания: {e}] "

        if "не удалось распознать текст" in segment_text.lower():
            continue

        if i > 0:
            segment_text = remove_overlap_duplicates(previous_segment_text, segment_text)

        recognized_text += " " + segment_text
        previous_segment_text = segment_text.split()

        os.remove(segment_path)

    return recognized_text


# Функция для удаления дубликатов на стыке фрагментов (перекрытие) с учетом частичного совпадения
def remove_overlap_duplicates(previous_segment_text: list, current_segment_text: str) -> str:
    overlap_count = 8

    previous_segment_text = previous_segment_text[-overlap_count:]
    previous_segment_text_lower = [word.lower() for word in previous_segment_text]

    current_segment_words = current_segment_text.split()
    current_segment_text = current_segment_words[:overlap_count]
    current_segment_text_lower = [word.lower() for word in current_segment_text]

    common_words = set(previous_segment_text_lower) & set(current_segment_text_lower)
    print(common_words)

    filtered_first_words = []
    for word in current_segment_text:
        if word.lower() in common_words and common_words:
            common_words.remove(word.lower())
        else:
            filtered_first_words.append(word)

    remaining_words = current_segment_words[overlap_count:]
    return " ".join(filtered_first_words + remaining_words)


# Функция для объединения всех строк в одну
def merge_lines(text: str) -> str:
    return ' '.join(text.splitlines())


# Функция для очистки текста от знаков препинания, приведения к нижнему регистру, замены ё на е и удаления лишних пробелов
def clean_text(text: str) -> str:
    text = text.replace('ё', 'е').replace('Ё', 'Е')
    text = re.sub(r'(?<=\w)-(?=\w)', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Функция для вычисления схожести слов с учетом Levenshtein Distance
def are_words_similar(word1: str, word2: str) -> bool:
    if (word1.endswith("ие") and word2.endswith("ье") and word1[:-2] == word2[:-2]) or \
            (word1.endswith("ье") and word2.endswith("ие") and word1[:-2] == word2[:-2]):
        return True
    if (word1.endswith("ия") and word2.endswith("ье") and word1[:-2] == word2[:-2]) or \
            (word1.endswith("ье") and word2.endswith("ия") and word1[:-2] == word2[:-2]):
        return True

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

    similarity = (intersection / union) * 100
    return round(similarity, 2)


# Функция для восстановления структуры текста с учетом оригинальных слов и пунктуации
def restore_structure_with_original_words(recognized_text: str, original_text: str) -> str:
    recognized_text = clean_text(recognized_text)

    recognized_words = recognized_text.split()
    original_lines = original_text.splitlines()

    structured_text = []
    recognized_index = 0

    for line in original_lines:
        line_words = re.findall(r'\w+|[^\w\s]', line)
        line_result = []

        for word in line_words:
            if re.match(r'[^\w\s]', word):
                continue

            if recognized_index < len(recognized_words):
                current_word = recognized_words[recognized_index]

                similarity = SequenceMatcher(None, word.lower(), current_word.lower()).ratio()
                if similarity >= 0.7:
                    line_result.append(current_word)
                    recognized_index += 1
                else:
                    line_result.append(current_word)
                    recognized_index += 1
            else:
                continue

        structured_text.append(" ".join(line_result))

    return "\n".join(structured_text)
