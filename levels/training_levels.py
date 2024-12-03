import re


def apply_difficulty_level(text: str, difficulty_level: int) -> str:
    """
    Применяет уровень сложности к тексту.
    Уровни:
    0: Базовый уровень (без изменений)
    1: Пропускается 1 буква (вторая) для слов из 3 и более букв
    2: Пропускаются 2 буквы (вторая и третья) для слов из 4 и более букв
    3: Пропущены все буквы, кроме первой и последней для слов из 4 и более букв
    4: Пропущены все буквы кроме первой буквы каждого слова
    """

    def apply_replacement(word: str, level: int) -> str:
        # Используем регулярное выражение для разделения слова на буквы и знаки
        match = re.match(r"([а-яА-ЯёЁa-zA-Z\-]+)(\W*)", word)
        if not match:
            return word

        core, punctuation = match.groups()
        word_len = len(core)

        if level == 0:  # Базовый уровень (текст без изменений)
            return core + punctuation

        if level == 1:  # Пропускаем вторую букву для слов из 3 и более букв
            if word_len == 1 or word_len == 2:
                return core + punctuation
            elif word_len >= 3:
                return core[0] + '-' + core[2:] + punctuation

        elif level == 2:  # Пропускаем 2 и 3 буквы для слов из 4 и более букв
            if word_len == 1 or word_len == 2:
                return core + punctuation
            elif word_len == 3:
                return core[0] + '-' + core[2] + punctuation
            elif word_len >= 4:
                return core[0] + '-' + '-' + core[3:] + punctuation

        elif level == 3:  # Пропускаем все буквы, кроме первой и последней для слов из 4 и более букв
            if word_len == 1 or word_len == 2:
                return core + punctuation
            elif word_len == 3:
                return core[0] + '-' + core[2] + punctuation
            elif word_len >= 4:
                return core[0] + '-' * (word_len - 2) + core[-1] + punctuation

        elif level == 4:  # Пропущена все буквы кроме первой буквы
            if word_len == 1:
                return core + punctuation
            else:
                return core[0] + '-' * (word_len - 1) + punctuation

        return core + punctuation

    # Обрабатываем каждое слово, сохраняя формат строк
    return '\n'.join([' '.join([apply_replacement(word, difficulty_level) for word in line.split()]) for line in text.split('\n')])
