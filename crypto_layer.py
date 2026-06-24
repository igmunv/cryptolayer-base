import threading
import sys
import time
import os
import uuid

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text

import module_manager

from config import *

session = PromptSession()


# Мессенджер
MESSENGER_CLASS = None

# ID собеседника
COMPANION_ID = None

# ID текущего узла
NODE_ID = None


def main():

    init()




    listener_thread = threading.Thread(target=listener)
    listener_thread.start()

    sender()


def init():

    # Создаем директорию с данными
    os.makedirs(DATA_DIR_PATH, exist_ok=True)

    # Настройка мессенджера
    messenger_config()

    # Генерация ID узла
    generate_node_id()

    # Передача друг другу Node ID

    # Проверка существования цифровой подписи для узла

    # Ветвеление*


    pass


# Конфигурация мессенджера
def messenger_config():

    # Выбор мессенджера
    module_manager.load()
    print_formatted_text(HTML(f'<ansiyellow>All messengers:</ansiyellow>\n'))
    print_formatted_text(HTML(f'{module_manager.get_modules_string()}'))
    while True:
        messenger_index = session.prompt(HTML(f'<ansiyellow>Choice messenger> </ansiyellow>')).strip()
        if not messenger_index.isdigit():
            error("Enter a number!")
            continue
        messenger_index = int(messenger_index)
        MESSENGER_CLASS = module_manager.get_module_by_index(messenger_index)
        if not MESSENGER_CLASS:
            error("Selected messenger does not exist!")
            continue
        break

    # ID собеседника
    COMPANION_ID = session.prompt(HTML('<ansiyellow>Companion ID></ansiyellow>')).strip()


# Генерация и получение ID узла
def generate_node_id():

    # Попытка прочитать ID

    if os.path.exists(NODE_ID_FILE_PATH):
        node_id_file_content = open(NODE_ID_FILE_PATH, encoding="utf-8").read().strip()
        if len(node_id_file_content) >= 64:
            NODE_ID = node_id_file_content
            return

    # Генерация ID
    new_node_id = ""
    for i in range(2):
        random_id = uuid.uuid4()
        new_node_id += random_id.hex

    with open(NODE_ID_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_node_id)

    NODE_ID = new_node_id


def sender():

    while True:

        with patch_stdout():
            user_input = session.prompt(HTML('<ansigreen>you></ansigreen> ')).strip()

        if user_input == ":":
            if not answer("<ansired>You want send this?</ansired>"):
                sender_console()
                continue


# Это консоль для управления программой
def sender_console():

    print_formatted_text("c - Continue\nq - Quit from CryptoLayer")

    while True:

        user_input = session.prompt(HTML('<ansiyellow>CMD ></ansiyellow>')).strip()

        if not user_input:
            continue

        if user_input == "c":
            return
        elif user_input == "q":
            sys.exit(0)
        else:
            error('Unknown command!')


def listener():
    msg = "Hello, how are you?"
    while True:
        with patch_stdout():
            print_formatted_text(HTML('<ansiblue>peer:</ansiblue> Hello'))
        time.sleep(5)


# Для вопросов
def answer(text, yes_default=False):
    if yes_default:
        user_input = session.prompt(HTML(f"{text} (y/N): ")).strip().lower()
        if not user_input:
            return True
    else:
        user_input = session.prompt(HTML(f"{text} (y/N): ")).strip().lower()
        if not user_input:
            return False

    if user_input in ["yes", "y"]:
        return True
    else:
        return False


def error(text):
    print_formatted_text(HTML(f'<ansired>{text}</ansired>'))


if __name__ == "__main__":
    main()
