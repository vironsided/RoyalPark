import secrets
import string


def generate_temp_password(length: int = 10) -> str:
    """
    Генерирует случайный пароль заданной длины.
    Использует только буквы (верхний и нижний регистр) и цифры.
    Примеры: fCMLqhzVSb, Kx9mP2vLq, F8nR5wT3Y
    """
    # Используем только буквы и цифры (без специальных символов)
    alphabet = string.ascii_letters + string.digits
    
    # Генерируем случайный пароль из букв и цифр
    return ''.join(secrets.choice(alphabet) for _ in range(length))
