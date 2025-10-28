"""
设置管理工具
"""
import json
import os


def load_settings():
    """加载系统设置"""
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认设置
        settings = {'marked_only': False}
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return settings


def save_settings(settings):
    """保存系统设置"""
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

