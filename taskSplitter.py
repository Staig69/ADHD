from gigachat import GigaChat
import os
import ssl
import certifi
from dotenv import load_dotenv


def split_tasks(task_description: str, time_minutes: int = 30, tasks_performed: str = None):
    load_dotenv()
    """
    Разбивает задачу на подзадачи
    """
    # Отключаем проверку SSL
    ssl._create_default_https_context = ssl._create_unverified_context

    prompt = f"Разбей следующую задачу на подзадачи, которые можно выполнить за {time_minutes} минут. "

    if tasks_performed is not None:
        prompt_middle = f"Уже сделаны подзадачи: {tasks_performed}. "
    else:
        prompt_middle = ""

    prompt_end = (
        "Выведи результат в виде списка, где каждая подзадача — отдельный пункт. "
        "Вывод должен содержать только подзадачи без всяких объяснений и без нумерации. "
        f"Задача: {task_description}"
    )

    prompt = prompt + prompt_middle + prompt_end
    with GigaChat(credentials=os.getenv("API_KEY"),verify_ssl_certs=False) as giga:
        try:
            response = giga.chat(prompt)
            answer = response.choices[0].message.content
            subtasks = [line.strip("*- ") for line in answer.split("\n") if line.strip()]
            return subtasks
        except Exception as e:
            return [f"Произошла ошибка при запросе к GigaChat: {e}"]
