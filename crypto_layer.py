import threading
import sys
import time
import os
import uuid
import logging
import getpass

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text
from prompt_toolkit.styles import Style

from colorama import Fore, Style as ColoramaStyle

from rich.console import Console

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

import module_manager
from base_module import BaseModule

from levels.application import Application
from levels.presentation import Presentation
from levels.transport import Transport
from levels.transitional import Transitional
from levels.base import Base

from config import *


pt_session = PromptSession()
console = Console()

# Мессенджер
MODULE_CLASS = None
MODULE_CLASS_SEND = None

# ID собеседника в мессенджере
COMPANION_ID = None

# ID текущего узла
NODE_ID = None

# Цифровая подпись
# Приватный ключ
SIGN_PRIVATE_KEY = None
# Публичный ключ
SIGN_PUBLIC_KEY = None

# Приватный ключ для ECC
MY_PRIVATE_KEY = None

# Ключ шифрования AES
AES_KEY = None

# NODE ID собеседника
COMPANION_NODE_ID = None

# подпись собеседника
COMPANION_SIGN = None

# ECC public key собеседника
COMPANION_PUBLIC_KEY = None

# Пароль пользователя
USER_PASSWORD = None

# Уровни
TRANSITIONAL_LEVEL = None
TRANSPORT_LEVEL = None
PRESENTATION_LEVEL = None
APPLICATION_LEVEL = None

TRANSITIONAL_LEVEL_INGESTER = None


def main():

    try:

        init()

        # здесь мы уже можем отправлять сообщения
        print_formatted_text(HTML(f'\n---------------------\n'))
        sender_text_box()

    except KeyboardInterrupt:
        print_formatted_text(HTML(f'\n---------------------\n'))
        console.print("\n[+] KeyboardInterrupt: [green]Done[/green]")

    finally:

        console.print("[!] Crypto Layer: [yellow]Shutting down...[/yellow]")

        Base.stop_event.set()
        BaseModule.stop_event.set()

        main_thread = threading.main_thread()
        for thread in threading.enumerate():
            if thread is not main_thread:
                thread.join()

        console.print("[+] Crypto Layer: [green]Bye![/green]")


def init():

    global USER_PASSWORD

    # Спрашиваем пароль
    upass = getpass.getpass("Your password: ")
    USER_PASSWORD = bytearray(upass.encode('utf-8'))
    del upass

    # Создаем директорию с данными
    os.makedirs(DATA_DIR_PATH, exist_ok=True)
    os.makedirs(KNOWN_NODES_DIR_PATH, exist_ok=True)

    # инциализация логера
    init_logger()

    # инциализация уровней
    init_levels()

    # Настройка мессенджера
    messenger_config()

    # - - РАБОТА С ПОДПИСЯМИ - -

    with console.status("[!] Signatures: [yellow]Loading...[/yellow]") as status:

        # Генерация ID узла
        generate_node_id()

        # Чтение или генерация цифровой подписи данного узла
        generate_signature(status)

        # Обмен ID узлов
        node_id_exchange(status)

        # Проверка существования цифровой подписи собеседника
        # Передача цифровой подписи
        # Затем спрашиваем у пользователя доверяем ли этой подписи, показывая первые 4 символа, и последние
        check_and_exchange_companion_sign(status)

    console.print("[+] Signatures: [green]Done[/green]")

    # удалить пароль пользователя из памяти, так как он уже не нужен
    remove_password_from_ram()

    # - - РАБОТА С КЛЮЧАМИ ШИФРОВАНИЯ - -

    with console.status("[!] Encryption: [yellow]Loading...[/yellow]") as status:

        # Генерация и обмен публичными ключами ECC
        generate_and_exchange_ecc_keys(status)

    console.print("[+] Encryption: [green]Done[/green]")

    # Может сделать отправку служебного сообщения, которое говорит о том что мы готовы к передаче. Это сообщение передается уже зашифрованым


def init_logger():

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s -> %(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # вывод логов в файл
    if LOGS_TO_FILE:
        file_handler = logging.FileHandler(
            LOGS_FILE_PATH, encoding="utf-8", mode="w"
        )
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

    # вывод логов в терминал
    if PRINT_LOGS:
        terminal_handler = logging.StreamHandler(sys.stdout)
        terminal_handler.setFormatter(log_format)
        root_logger.addHandler(terminal_handler)



def init_levels():

    global TRANSITIONAL_LEVEL
    global TRANSPORT_LEVEL
    global PRESENTATION_LEVEL
    global APPLICATION_LEVEL

    global TRANSITIONAL_LEVEL_INGESTER

    with console.status("[!] Levels: [yellow]Loading...[/yellow]") as status:

        APPLICATION_LEVEL = Application()
        PRESENTATION_LEVEL = Presentation()
        TRANSPORT_LEVEL = Transport()
        TRANSITIONAL_LEVEL = Transitional()
        TRANSITIONAL_LEVEL_INGESTER = TRANSITIONAL_LEVEL.receive

        status.update("[!] Levels: [yellow]Level class objects created[/yellow]")

        APPLICATION_LEVEL.update_levels(sys.modules[__name__], PRESENTATION_LEVEL)
        PRESENTATION_LEVEL.update_levels(APPLICATION_LEVEL, TRANSPORT_LEVEL)
        TRANSPORT_LEVEL.update_levels(PRESENTATION_LEVEL, TRANSITIONAL_LEVEL)

    console.print("[+] Levels: [green]Done[/green]")


# Конфигурация мессенджера
def messenger_config():

    global COMPANION_ID
    global MODULE_CLASS
    global TRANSITIONAL_LEVEL_INGESTER

    # Выбор мессенджера
    module_manager.load()

    print_formatted_text(HTML(f'\n - - Modules (Messengers) - -'))
    print_formatted_text(HTML(f'{module_manager.get_modules_string()}'))
    while True:
        messenger_index = input(f'Choice module: {Fore.GREEN}').strip()
        print(ColoramaStyle.RESET_ALL, end="")
        if not messenger_index.isdigit():
            error("Enter a number!")
            continue
        messenger_index = int(messenger_index)
        MODULE_CLASS = module_manager.get_module_by_index(messenger_index)
        if not MODULE_CLASS:
            error("Selected messenger does not exist!")
            continue
        break

    # ID собеседника
    COMPANION_ID = input(f'Companion ID (in module): {Fore.GREEN}').strip()
    print(ColoramaStyle.RESET_ALL, end="")

    # Спрашиваем у пользователя Credentials
    creds = []
    print_formatted_text(HTML(f'\n - - Credentials - -\n'))
    all_module_creds = MODULE_CLASS.get_exp_creds()
    for n, cred in enumerate(all_module_creds):
        if len(all_module_creds) > 1:
            print_formatted_text(HTML(f"{n+1}/{len(all_module_creds)}. '{cred.name}' - {cred.description}"))
        else:
            print_formatted_text(HTML(f"'{cred.name}' - {cred.description}"))
        user_cred = getpass.getpass(f'{cred.name}: ').strip()
        print(ColoramaStyle.RESET_ALL, end="")
        print()
        creds.append(user_cred)

    # Создаем сессию в модуле мессенджера
    MODULE_CLASS.create_session(creds, TRANSITIONAL_LEVEL_INGESTER, COMPANION_ID)
    TRANSITIONAL_LEVEL.update_levels(TRANSPORT_LEVEL, MODULE_CLASS.sender)


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
def generate_signature(status):

    global SIGN_PRIVATE_KEY
    global SIGN_PUBLIC_KEY

    # файл нашей подписи есть
    if os.path.exists(SIGN_PRIVATE_FILE_PATH):

        status.update("[!] Signatures: [yellow]Our signature file exists[/yellow]")

        with open(SIGN_PRIVATE_FILE_PATH, "rb") as f:
            loaded_pem_data = f.read()

        # если файл не пустой
        if loaded_pem_data:

            status.update("[!] Signatures: [yellow]Signature file not empty. Use this signature[/yellow]")

            SIGN_PRIVATE_KEY = serialization.load_pem_private_key(
                loaded_pem_data,
                password=bytes(USER_PASSWORD)
            )

            SIGN_PUBLIC_KEY = SIGN_PRIVATE_KEY.public_key()

            return

        else:
            status.update("[!] Signatures: [yellow]Signature file empty[/yellow]")


    # ... генерация
    status.update("[!] Signatures: [yellow]Generate new our signature...[/yellow]")

    SIGN_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
    SIGN_PUBLIC_KEY = SIGN_PRIVATE_KEY.public_key()

    # Сохранение приватного ключа в файл в зашифрованном виде

    pem_private_data = SIGN_PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(bytes(USER_PASSWORD))
    )

    status.update("[!] Signatures: [yellow]Write new signature in file[/yellow]")

    # Записываем байты в файл
    with open(SIGN_PRIVATE_FILE_PATH, "wb") as f:
        f.write(pem_private_data)


# Обмен ID узлов
def node_id_exchange(status):

    status.update("[!] Signatures: [yellow]Sending our node id. Starting the exchange of node id...[/yellow]")

    # Передача друг другу Node ID
    # Ожидаем NODE ID собеседника
    TIMER_NODE_ID_EXCHANGE = 5.0
    while not COMPANION_NODE_ID:
        status.update("[!] Signatures: [yellow]Waiting for companion node id...[/yellow]")
        # !!!!!!!! нужно сделать так чтобы если долго не приходит то отправить заново свой и ждать. нужно сделать так везде во всех while
        if TIMER_NODE_ID_EXCHANGE >= 5.0:
            APPLICATION_LEVEL.send_my_node_id(NODE_ID)
            TIMER_NODE_ID_EXCHANGE = 0.0
        time.sleep(0.1)
        TIMER_NODE_ID_EXCHANGE += 0.1

    # print("COMPANION_NODE_ID", "=", COMPANION_NODE_ID)


# Проверка существования цифровой подписи собеседника и обмен ею
def check_and_exchange_companion_sign(status):

    global COMPANION_SIGN

    try:

        COMPANION_SIGN_FILE_PATH = os.path.join(KNOWN_NODES_DIR_PATH, COMPANION_NODE_ID)

        # цифровая подпись существует
        # достаем из файла и расшифровываем ее
        if os.path.exists(COMPANION_SIGN_FILE_PATH):

            status.update("[!] Signatures: [yellow]Сompanion signature exists[/yellow]")

            # Чтение подписи собеседника из файла
            status.update("[!] Signatures: [yellow]Reading companion signature from file...[/yellow]")

            with open(COMPANION_SIGN_FILE_PATH, "rb") as f:
                file_content = f.read()

            salt = file_content[:16]
            nonce = file_content[16:28]
            encrypted_data = file_content[28:]

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=b"public-key-encryption",
            )
            up_aes_key = hkdf.derive(USER_PASSWORD)

            aesgcm = AESGCM(up_aes_key)
            pem_public_bytes = aesgcm.decrypt(nonce, encrypted_data, associated_data=None)

            loaded_public_key = serialization.load_pem_public_key(pem_public_bytes)

            # ждем, так как собеседник может отправить свою подпись
            # !!! нужно переделать. и сделать так что если чел отправил подпись, в любой момент, то мы ее применяем
            status.update("[!] Signatures: [yellow]Waiting to see if companion sends signature...[/yellow]")
            time.sleep(5)

            # если собеседник не отправил свою подпись, то значит та которая в файле - актуальна
            if not COMPANION_SIGN:
                COMPANION_SIGN = loaded_public_key
                return

            # если не существует то мы отправляем собеседнику свою подпись, а он в ответ должен отправить свою подпись.
            # далее уже происходит проверка подписей
        else:
            status.update("[!] Signatures: [yellow]Сompanion signature does not exists[/yellow]")

        sign_public_bytes_X962 = SIGN_PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )

        status.update("[!] Signatures: [yellow]Sending our signature. Starting the exchange of signatures...[/yellow]")

        APPLICATION_LEVEL.send_my_sign(sign_public_bytes_X962)

        # Если код продолжается, то значит что новая подпись пришла или же подписи просто нет в файле, и нужно получить новую подпись от собеседника и записать ее в файл

        while not COMPANION_SIGN:
            status.update("[!] Signatures: [yellow]Waiting for companion signature...[/yellow]")
            time.sleep(5)

        status.stop()

        # Вывод подписи пользователя
        print_formatted_text(HTML(f'Your signature (show this to companion):\n| <ansiyellow>{get_firts_last_4_chars_sign(SIGN_PUBLIC_KEY)}</ansiyellow>\n'))
        # Вывод подписи собеседника
        print_formatted_text(HTML(f'Companion signature (сheck for correctness):\n| <ansiyellow>{get_firts_last_4_chars_sign(COMPANION_SIGN)}</ansiyellow>\n'))
        # Проверка подписи собеседника пользователем
        if answer(f"Is the companion signature correct?"):

            print()
            status.start()

            # Доверяем, записываем, используем эту подпись

            # Зашифровываем публичную подпись собеседника паролем

            status.update("[!] Signatures: [yellow]Save companion signature in file...[/yellow]")

            pem_public_bytes = COMPANION_SIGN.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            salt = os.urandom(16)
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=b"public-key-encryption",
            )
            up_aes_key = hkdf.derive(USER_PASSWORD)

            aesgcm = AESGCM(up_aes_key)
            nonce = os.urandom(12)
            encrypted_public_data = aesgcm.encrypt(nonce, pem_public_bytes, associated_data=None)

            # В файл сохраняем уже зашифрованную подпись

            with open(COMPANION_SIGN_FILE_PATH, "wb") as f:
                f.write(salt + nonce + encrypted_public_data)

        else:
            print()
            raise TypeError("do not trust the signature")

    except Exception as e:
        # ЭТО ВРЕМЕННО!
        print(e)
        raise Exception(e)

    finally:
        TRANSITIONAL_LEVEL.SIGN_PRIVATE_KEY = SIGN_PRIVATE_KEY
        TRANSITIONAL_LEVEL.COMPANION_SIGN_PUBLIC_KEY = COMPANION_SIGN # обновляем подпись собеседника
        TRANSITIONAL_LEVEL.DO_SIGN = True # ОБЯЗАТЕЛЬНО!!! Так как теперь используется подпись


# Генерация и обмен публичными ключами, вычисление симметриного ключа
def generate_and_exchange_ecc_keys(status):

    # Генерация пары ключей
    status.update("[!] Encryption: [yellow]Generate keys...[/yellow]")
    MY_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
    my_public_key = MY_PRIVATE_KEY.public_key()
    my_pkey_bytes = my_public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )

    # Передача публичного ключа
    status.update("[!] Encryption: [yellow]Sending public key. Starting the exchange of public keys...[/yellow]")
    APPLICATION_LEVEL.send_my_public_key(my_pkey_bytes)

    # Ожидаем публичный ключ от собеседника
    while not COMPANION_PUBLIC_KEY:
        status.update("[!] Encryption: [yellow]Waiting for companion public key...[/yellow]")
        time.sleep(5)

    # Вычисление симетричного ключа
    status.update("[!] Encryption: [yellow]Symmetric key computation...[/yellow]")
    AES_KEY = MY_PRIVATE_KEY.exchange(ec.ECDH(), COMPANION_PUBLIC_KEY)

    PRESENTATION_LEVEL.DO_ENCRYPT = True
    PRESENTATION_LEVEL.AES_KEY = AES_KEY





def receive_node_id(node_id: str):
    global COMPANION_NODE_ID
    COMPANION_NODE_ID = node_id


def receive_sign(sign: bytes):
    global COMPANION_SIGN
    COMPANION_SIGN = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(),
        sign
    )
    # получаем подпись и тут же проверяем, обновляем и применяем ее


def receive_public_key(public_key: bytes):
    global COMPANION_PUBLIC_KEY
    COMPANION_PUBLIC_KEY = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(),
        public_key
    )


def receive_text(text: str):
    with patch_stdout():
        print_formatted_text(HTML(f'<ansiblue>peer:</ansiblue> {text}'))





def sender_text_box():

    while True:

        with patch_stdout():
            user_input = pt_session.prompt(HTML('<ansigreen>you></ansigreen> ')).strip()

        if user_input == ":":
            if not answer("<ansired>You want send this?</ansired>"):
                sender_console()
                continue

        APPLICATION_LEVEL.send_text(user_input)


# Это консоль для управления программой
def sender_console():

    print_formatted_text("c - Continue\nq - Quit from CryptoLayer")

    while True:

        user_input = pt_session.prompt(HTML('<ansiyellow>CMD ></ansiyellow>')).strip()

        if not user_input:
            continue

        if user_input == "c":
            return
        elif user_input == "q":
            sys.exit(0)
        else:
            error('Unknown command!')


def remove_password_from_ram():
    for i in range(len(USER_PASSWORD)):
        USER_PASSWORD[i] = 0


def get_firts_last_4_chars_sign(sign):

    sign_public_bytes_pem = sign.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )

    first_4 = sign_public_bytes_pem[:4]
    last_4 = sign_public_bytes_pem[-4:]
    return f"{first_4.hex()}...{last_4.hex()}"



# Для вопросов
def answer(text, yes_default=False):
    if yes_default:
        user_input = pt_session.prompt(HTML(f"{text} (y/N): ")).strip().lower()
        if not user_input:
            return True
    else:
        user_input = pt_session.prompt(HTML(f"{text} (y/N): ")).strip().lower()
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
