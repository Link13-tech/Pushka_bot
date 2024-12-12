import os

import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()


def generate_auth_url():
    """Генерирует URL для авторизации пользователя через ВКонтакте."""
    params = {
        "client_id": os.getenv("VK_APP_ID"),
        "redirect_uri": os.getenv("REDIRECT_URI"),
        "scope": "wall,docs, audio",
        "response_type": "code",
        "v": os.getenv("VK_API_VERSION"),
    }
    return f"https://oauth.vk.com/authorize?{urlencode(params)}"


def exchange_code_for_token(code):
    """Обменивает код авторизации на access_token."""
    url = "https://oauth.vk.com/access_token"
    params = {
        "client_id": os.getenv("VK_APP_ID"),
        "client_secret": os.getenv("VK_APP_SECRET"),
        "redirect_uri": os.getenv("REDIRECT_URI"),
        "code": code,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "access_token" in data:
        access_token = data["access_token"]
        vk_user_id = data["user_id"]

        # Теперь проверим разрешения токена
        check_permissions(access_token)

        return access_token, vk_user_id
    else:
        raise Exception(f"Ошибка получения токена: {data}")


def check_permissions(access_token):
    """Проверяет разрешения токена."""
    url = "https://api.vk.com/method/users.get"
    params = {
        "access_token": access_token,
        "v": "5.131"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "response" in data:
        print(f"Разрешения токена: {data['response']}")
    else:
        print(f"Ошибка при проверке разрешений: {data}")
