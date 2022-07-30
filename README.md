# yatube

## Описание:
Социальная сеть для блогеров.
Реализована регистрация пользователей, с возможностью смены и восстановления пароля через почту.
Используется пагинация и кэширование страниц. Реализованы подписки на авторов. Сделано покрытие тестами.

## Технологии:
Python 3.7, 
Django 2.2.19, 
PostgreSQL

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/E-bean/yatube
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:
```
cd yatube
```

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
