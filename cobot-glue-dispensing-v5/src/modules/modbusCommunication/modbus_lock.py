# modbus_lock.py
import threading

modbus_lock: threading.Lock = threading.Lock()
"""
Глобален lock обект за синхронизация на Modbus комуникацията.

Този lock се използва, за да се гарантира, че само една нишка (thread)
изпълнява Modbus операции в даден момент. Това предотвратява
конфликти и грешки при едновременен достъп до сериен порт.

Пример за употреба:
    from modbus_lock import modbus_lock

    with modbus_lock:
        # Извършете Modbus операция
        client.write_register(1, 123)
"""
