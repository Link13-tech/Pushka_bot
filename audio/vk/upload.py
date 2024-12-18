import tempfile
import logging
import requests
import os

logging.basicConfig(level=logging.INFO)


def get_upload_url(access_token):
    """Запрашивает URL для загрузки аудиофайла на сервер ВКонтакте."""
    url = "https://api.vk.com/method/docs.getUploadServer"
    params = {
        "access_token": access_token,
        "type": "audio_message",
        "v": "5.131",
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "response" in data:
        logging.info("Получен upload_url для загрузки аудио.")
        return data["response"]["upload_url"]
    else:
        raise Exception(f"Ошибка получения upload_url: {data}")


def generate_storage_url(bucket_name, user_id, poem_id,  level):
    """
    Генерирует URL файла в Yandex Object Storage с уникальной структурой папок.
    :param bucket_name: Имя бакета в Object Storage
    :param poem_id: ID стиха
    :param user_id: ID пользователя в Telegram
    :param level: Уровень пользователя
    :return: URL файла
    """

    # Генерация URL для файла в объектном хранилище
    return f"https://storage.yandexcloud.net/{bucket_name}/voice_messages/{user_id}/{poem_id}/{user_id}_{poem_id}_{level}_voice.ogg"


def download_file_from_yandex(storage_url):
    """
    Скачивает файл из Yandex Object Storage.
    :param storage_url: URL файла в Object Storage
    :return: Путь к временно скачанному файлу
    """
    response = requests.get(storage_url, stream=True)
    if response.status_code == 200:
        # Создаем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        with open(temp_file.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return temp_file.name
    else:
        raise Exception(f"Ошибка скачивания файла: {response.status_code}, {response.text}")


def upload_audio_file_from_yandex(upload_url, bucket_name, user_id, poem_id, level):
    """
    Генерирует URL файла, скачивает его с Yandex Object Storage и загружает на сервер ВКонтакте.
    :param upload_url: URL для загрузки на ВКонтакте
    :param bucket_name: Имя бакета в Object Storage
    :param user_id: ID пользователя
    :param poem_id: ID стиха
    :param level: Уровень
    :return: Параметр file для сохранения
    """
    local_file_path = None  # Инициализация переменной
    try:
        # Генерируем URL файла в Yandex Object Storage
        storage_url = generate_storage_url(bucket_name, user_id, poem_id, level)

        # Скачиваем файл с Yandex Object Storage
        local_file_path = download_file_from_yandex(storage_url)

        # Загружаем файл на сервер ВКонтакте
        with open(local_file_path, "rb") as f:
            response = requests.post(upload_url, files={"file": f})
            data = response.json()

        if "file" in data:
            return data["file"]
        else:
            raise Exception(f"Ошибка загрузки файла: {data}")
    finally:
        if local_file_path and os.path.exists(local_file_path):
            os.remove(local_file_path)


def save_audio_file(access_token, file_param):
    """Сохраняет загруженный аудиофайл на сервере ВКонтакте."""
    url = "https://api.vk.com/method/docs.save"
    params = {
        "access_token": access_token,
        "file": file_param,
        "v": "5.131",
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "response" in data:
        logging.info("Аудиофайл успешно сохранён.")
        return data["response"]["audio_message"]
    else:
        raise Exception(f"Ошибка сохранения файла: {data}")
