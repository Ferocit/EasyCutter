import json
import os


def settings_path():
    base = os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), '.config')
    return os.path.join(base, 'EasyCutter', 'settings.json')


def load_settings(path=None):
    try:
        with open(path or settings_path(), encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(settings, path=None):
    path = path or settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def unique_path(path):
    """Gibt `path` zurück oder, falls die Datei schon existiert, `name_2.ext`, `name_3.ext` usw."""
    base, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(path):
        path = f'{base}_{n}{ext}'
        n += 1
    return path
