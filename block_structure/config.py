import os
import json

# Режимы блокировки
MODE_HARD = "hard"
MODE_SOFT = "soft"

# Текущий режим (используем список для возможности изменения из других модулей)
CURRENT_MODE = [MODE_SOFT]

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(BASE_DIR, "block_config.json")
HTML_FILE_PATH = os.path.join(BASE_DIR, "block_page.html")
REDIRECT_URL = f"file:///{HTML_FILE_PATH.replace('\\', '/')}"


# Загружаем конфиг из JSON
def load_config():
    """Загрузить конфигурацию из JSON файла"""
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return {
            'apps': config.get('apps', []),
            'sites': config.get('sites', []),
            'check_interval': config.get('check_interval', 2),
            'warning_cooldown': config.get('warning_cooldown', 60)
        }
    except FileNotFoundError:
        print(f"⚠️ Файл конфигурации не найден: {CONFIG_FILE_PATH}")
        print("⚠️ Создаем файл с настройками по умолчанию...")
        return create_default_config()
    except json.JSONDecodeError:
        print(f"⚠️ Ошибка чтения JSON файла: {CONFIG_FILE_PATH}")
        return create_default_config()


def create_default_config():
    """Создать конфиг по умолчанию"""
    default_config = {
        "apps": [
            "steam.exe",
            "Telegram.exe",
            "Discord.exe"
        ],
        "sites": [
            "Telegram",
            "YouTube",
            "ВКонтакте",
            "Лента новостей",
            "Wildberries",
            "Ozon",
            "Reddit",
            "WhatsApp",
            "Мессенджер"
        ],
        "check_interval": 2,
        "warning_cooldown": 60
    }

    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✓ Создан файл конфигурации: {CONFIG_FILE_PATH}")
    except Exception as e:
        print(f"❌ Ошибка создания файла конфигурации: {e}")

    return default_config


def save_config(config_data=None):
    """Сохранить текущую конфигурацию в JSON файл"""
    if config_data is None:
        config_data = {
            "mode": CURRENT_MODE,
            "apps": BLOCK_APPS,
            "sites": BLOCK_SITES,
            "check_interval": CHECK_INTERVAL,
            "warning_cooldown": WARNING_COOLDOWN
        }

    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False


# Загружаем конфигурацию при старте
_config = load_config()
BLOCK_APPS = _config['apps']
BLOCK_SITES = _config['sites']
CHECK_INTERVAL = _config['check_interval']
WARNING_COOLDOWN = _config['warning_cooldown']


def reload_config():
    """Перезагрузить конфигурацию"""
    global BLOCK_APPS, BLOCK_SITES, CHECK_INTERVAL, WARNING_COOLDOWN
    _config = load_config()
    BLOCK_APPS = _config['apps']
    BLOCK_SITES = _config['sites']
    CHECK_INTERVAL = _config['check_interval']
    WARNING_COOLDOWN = _config['warning_cooldown']


def get_mode():
    """Получить текущий режим"""
    return CURRENT_MODE[0]


def set_mode(mode):
    """Установить режим"""
    CURRENT_MODE[0] = mode


def is_hard_mode():
    """Проверить, включен ли жесткий режим"""
    return CURRENT_MODE[0] == MODE_HARD


def is_soft_mode():
    """Проверить, включен ли упрощенный режим"""
    return CURRENT_MODE[0] == MODE_SOFT


def get_blocked_apps():
    """Получить список блокируемых приложений"""
    return BLOCK_APPS


def get_blocked_sites():
    """Получить список блокируемых сайтов"""
    return BLOCK_SITES


def add_blocked_app(app_name):
    """Добавить приложение в список блокировки"""
    # Проверяем без учета регистра
    if app_name.lower() not in [app.lower() for app in BLOCK_APPS]:
        BLOCK_APPS.append(app_name)
        return save_config()
    return False

def remove_blocked_app(app_name):
    """Удалить приложение из списка блокировки"""
    # Ищем без учета регистра
    for app in BLOCK_APPS:
        if app.lower() == app_name.lower():
            BLOCK_APPS.remove(app)
            return save_config()
    return False

def add_blocked_site(site_name):
    """Добавить сайт в список блокировки"""
    # Проверяем без учета регистра
    if site_name.lower() not in [site.lower() for site in BLOCK_SITES]:
        BLOCK_SITES.append(site_name)
        return save_config()
    return False

def remove_blocked_site(site_name):
    """Удалить сайт из списка блокировки"""
    # Ищем без учета регистра
    for site in BLOCK_SITES:
        if site.lower() == site_name.lower():
            BLOCK_SITES.remove(site)
            return save_config()
    return False

def toggle_mode():
    """Переключить режим и сохранить"""
    if CURRENT_MODE == MODE_SOFT:
        return set_mode(MODE_HARD)
    else:
        return set_mode(MODE_SOFT)