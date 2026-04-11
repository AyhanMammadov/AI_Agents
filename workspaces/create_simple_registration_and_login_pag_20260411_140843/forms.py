import re

def validate_registration(name, email, password, confirm):
    errors = {}
    if not name:
        errors['name'] = 'Имя обязательно.'
    if not email:
        errors['email'] = 'Email обязателен.'
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors['email'] = 'Некорректный email.'
    if not password or len(password) < 6:
        errors['password'] = 'Пароль должен быть не менее 6 символов.'
    if password != confirm:
        errors['confirm'] = 'Пароли не совпадают.'
    return errors

def validate_login(email, password):
    errors = {}
    if not email:
        errors['email'] = 'Email обязателен.'
    if not password:
        errors['password'] = 'Пароль обязателен.'
    return errors
