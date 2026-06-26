import threading
import sys
import time
import os
import uuid

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

import module_manager
import sender
import listener
import packet

from config import *


pt_session = PromptSession()


# Мессенджер
MESSENGER_CLASS = None

# ID собеседника
COMPANION_ID = None

# ID текущего узла
NODE_ID = None

# Цифровая подпись
# Приватный ключ
SIGN_PRIVATE_KEY = None
# Публичный ключ
SIGN_PUBLIC_KEY = None

# Ключ шифрования AES
AES_KEY = None


LISTENER = None
SENDER = None


def main():

    init()

    # sndr.send_comunic(packet.DataTypes.TEXT.value, "Learning English effectively requires daily immersion and steady practice across all four core skills: listening, speaking, reading, and writing. The fastest path to fluency involves surrounding yourself with the language—consume native content, practice speaking out loud every day, and focus on practical, consistent routines rather than just memorizing grammar.Память: Требует много оперативной памяти. Важно учитывать, что распаковка файлов, сжатых на 22-м уровне, также потребует больше ОЗУ, чем при использовании низких уровней.".encode())


    # listener_thread = threading.Thread(target=listener)
    # listener_thread.start()
    #
    # sender()


def init():

    # Создаем директорию с данными
    os.makedirs(DATA_DIR_PATH, exist_ok=True)

    # Настройка мессенджера
    messenger_config()

    # Генерация ID узла
    generate_node_id()

    # Чтение или генерация цифровой подписи данного узла
    generate_signature()


    # - - РАБОТА С ПОДПИСЯМИ - -


    # Передача друг другу Node ID
    print("SENDER.send_node_id(NODE_ID)")
    SENDER.send_node_id(NODE_ID)

    # Передача цифровой подписи

    # Проверка существования цифровой подписи собеседника

    # Затем спрашиваем у пользователя доверяем ли этой подписи, показывая первые 4 символа, и последние

    # Ветвеление*


    # - - РАБОТА С КЛЮЧАМИ ШИФРОВАНИЯ - -


    # Генерация публичного ключа

    # Передача публичного ключа

    # Вычисление симетричного ключа


# Конфигурация мессенджера
def messenger_config():

    global COMPANION_ID
    global MESSENGER_CLASS
    global LISTENER
    global SENDER

    # Выбор мессенджера
    module_manager.load()
    print_formatted_text(HTML(f'<ansiyellow>All messengers:</ansiyellow>\n'))
    print_formatted_text(HTML(f'{module_manager.get_modules_string()}'))
    while True:
        messenger_index = pt_session.prompt(HTML(f'<ansiyellow>Choice messenger> </ansiyellow>')).strip()
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
    COMPANION_ID = pt_session.prompt(HTML('<ansiyellow>Companion ID> </ansiyellow>')).strip()

    # Спрашиваем у пользователя Credentials
    creds = []
    print_formatted_text(HTML(f'<ansiyellow>Enter credentials:</ansiyellow>\n'))
    for n, cred in enumerate(MESSENGER_CLASS.get_exp_creds()):
        print_formatted_text(HTML(f"<ansiyellow>{n+1}. '{cred.name}' - {cred.description}</ansiyellow>\n"))
        user_cred = pt_session.prompt(HTML(f'<ansiyellow>{cred.name}> </ansiyellow>')).strip()
        creds.append(user_cred)

    # Создание Listener
    LISTENER = listener.Listener(0, 0, pt_session, ready_data_ingester)

    # Создаем сессию в модуле мессенджера
    MESSENGER_CLASS.create_session(creds, LISTENER.ingester, COMPANION_ID)

    # Создание Sender
    SENDER = sender.Sender(0, SIGN_PRIVATE_KEY, MESSENGER_CLASS.sender.send)


# Генерация или получение ID узла
def generate_node_id():

    global NODE_ID

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


# Генерация или получение цифровой подписи данного узла
def generate_signature():

    global SIGN_PRIVATE_KEY
    global SIGN_PUBLIC_KEY

    password = b"USER_PASSWORD!!!"

    if os.path.exists(SIGN_PRIVATE_FILE_PATH):

        with open(SIGN_PRIVATE_FILE_PATH, "rb") as f:
            loaded_pem_data = f.read()

        if loaded_pem_data:

            SIGN_PRIVATE_KEY = serialization.load_pem_private_key(
                loaded_pem_data,
                password=password
            )

            SIGN_PUBLIC_KEY = SIGN_PRIVATE_KEY.public_key()

            return


    # ... генерация

    SIGN_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())

    # Сохранение приватного ключа в файл в зашифрованном виде

    pem_private_data = SIGN_PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )

    # Записываем байты в файл
    with open(SIGN_PRIVATE_FILE_PATH, "wb") as f:
        f.write(pem_private_data)


# Принимает готовые данные от Listener
# а именно PayloadPacket
def ready_data_ingester(pack_type, payload_packet: packet.PayloadPacket):

    if pack_type == packet.PackTypes.SERVICE.value:

        print(packet.CMDTypes(payload_packet.pack_type).name)
        print(payload_packet.payload)

        if payload_packet.pack_type == packet.CMDTypes.MY_NODE_ID:
            pass

        # если получили node_id и подпись, то DO_SIGN = True
        # если получили public_key, то DO_ENCRYPT = True


    elif pack_type == packet.PackTypes.COMMUNIC.value:

        if payload_packet.pack_type == packet.DataTypes.TEXT.value:

            with patch_stdout():
                print_formatted_text(HTML(f'<ansiblue>peer:</ansiblue> {payload_packet.payload.decode()}'))

        else:
            print("Not TEXT data type:\n", payload_packet.payload)











def sender1():

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


def listener1():
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
