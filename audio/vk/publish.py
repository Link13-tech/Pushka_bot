import requests


def publish_post(owner_id, message, attachment, access_token):
    """Публикует запись на стене пользователя."""
    url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": owner_id,
        "message": message,
        "attachments": attachment,
        "access_token": access_token,
        "v": "5.131",
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "response" in data:
        return data["response"]["post_id"]
    else:
        raise Exception(f"Ошибка публикации записи: {data}")
