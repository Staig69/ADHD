from gigachat import GigaChat
import os
import ssl
import certifi
from dotenv import load_dotenv


def split_tasks(task_description: str):
    load_dotenv()
    """
    Разбивает задачу на подзадачи по 30 минут, используя официальный SDK.
    """
    # Отключаем проверку SSL
    ssl._create_default_https_context = ssl._create_unverified_context

    with GigaChat(
            credentials=os.getenv("API_KEY"),
            verify_ssl_certs=False  # Отключаем проверку SSL
    ) as giga:
        prompt = (
            "Разбей следующую задачу на подзадачи, которые можно выполнить за 30 минут. "
            "Выведи результат в виде списка, где каждая подзадача — отдельный пункт. "
            "Вывод должен содержать только подзадачи без всяких объяснений и не должен содержать в начале сообщения что ты понял задачу"
            f"Задача: {task_description}"
        )

        try:
            response = giga.chat(prompt)
            answer = response.choices[0].message.content
            subtasks = [line.strip("*- ") for line in answer.split("\n") if line.strip()]
            return subtasks
        except Exception as e:
            return [f"Произошла ошибка при запросе к GigaChat: {e}"]
