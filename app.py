#!/usr/bin/env python3
"""
DeepAgents GUI v2.0 - Модульная архитектура
Главный файл запуска приложения

Функционал:
- Чат с AI агентом (интеграция с LM Studio)
- Менеджер инструментов (включение/выключение)
- Менеджер агентов (создание суб-агентов)
- Статистика и логи системы
- Настройки и справка
"""

import sys
import logging
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deepagents.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Точка входа в приложение."""
    logger.info("Запуск DeepAgents GUI v2.0")
    
    try:
        from gui.main_window import DeepAgentsMainWindow
        
        app = DeepAgentsMainWindow()
        logger.info("GUI успешно инициализирован")
        
        app.mainloop()
        
        logger.info("Приложение завершено")
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        print(f"\n❌ Ошибка: Не удалось загрузить модули GUI")
        print(f"Проверьте установку зависимостей: pip install -r requirements.txt\n")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
