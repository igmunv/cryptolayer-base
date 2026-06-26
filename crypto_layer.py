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
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

import module_manager
import sender
import listener
import packet
import getpass

from config import *


pt_session = PromptSession()


# Мессенджер
MESSENGER_CLASS = None

# ID собеседника в мессенджере
COMPANION_ID = None

# ID текущего узла
NODE_ID = None

# Цифровая подпись
# Приватный ключ
SIGN_PRIVATE_KEY = None
# Публичный ключ
SIGN_PUBLIC_KEY = None

MY_PRIVATE_KEY = None

# Ключ шифрования AES
AES_KEY = None


LISTENER = None
SENDER = None


# NODE ID собеседника
COMPANION_NODE_ID = None

# подпись собеседника
COMPANION_SIGN = None

# ECC public key собеседника
COMPANION_PUBLIC_KEY = None


USER_PASSWORD = None


def main():

    init()

    # sndr.send_comunic(packet.DataTypes.TEXT.value, "Learning English effectively requires daily immersion and steady practice across all four core skills: listening, speaking, reading, and writing. The fastest path to fluency involves surrounding yourself with the language—consume native content, practice speaking out loud every day, and focus on practical, consistent routines rather than just memorizing grammar.Память: Требует много оперативной памяти. Важно учитывать, что распаковка файлов, сжатых на 22-м уровне, также потребует больше ОЗУ, чем при использовании низких уровней.".encode())


    # listener_thread = threading.Thread(target=listener)
    # listener_thread.start()
    #
    # sender()


def init():

    global USER_PASSWORD

    # Спрашиваем пароль
    upass = getpass.getpass("Your password: ")
    USER_PASSWORD = bytearray(upass.encode('utf-8'))
    del upass

    # Создаем директорию с данными
    os.makedirs(DATA_DIR_PATH, exist_ok=True)

    # Настройка мессенджера
    messenger_config()

    # Генерация ID узла
    generate_node_id()

    # - - РАБОТА С ПОДПИСЯМИ - -
    print_formatted_text(HTML(f'\n - - SIGNATURES - - \n'))

    # Чтение или генерация цифровой подписи данного узла
    generate_signature()

    # Передача друг другу Node ID
    SENDER.send_node_id(NODE_ID)

    # Ожидаем NODE ID собеседника
    while not COMPANION_NODE_ID:
        time.sleep(0.1)

    # print("COMPANION_NODE_ID", "=", COMPANION_NODE_ID)

    # Проверка существования цифровой подписи собеседника
    # Передача цифровой подписи
    # Затем спрашиваем у пользователя доверяем ли этой подписи, показывая первые 4 символа, и последние
    check_and_get_companion_sign()

    remove_password_from_ram()

    SENDER.update_sign_private_key(SIGN_PRIVATE_KEY)
    LISTENER.companion_public_key = COMPANION_SIGN # обновляем подпись собеседника
    LISTENER.DO_SIGN = True # ОБЯЗАТЕЛЬНО!!! Так как теперь используется подпись

    # - - РАБОТА С КЛЮЧАМИ ШИФРОВАНИЯ - -
    print_formatted_text(HTML(f'\n - - ENCRYPTION KEYS - - \n'))

    # Генерация и обмен публичными ключами
    generate_and_exchange_ecc_keys()

    # LISTENER.DO_ENCRYPT # Не забыть раскомментировать!


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

    if os.path.exists(SIGN_PRIVATE_FILE_PATH):

        with open(SIGN_PRIVATE_FILE_PATH, "rb") as f:
            loaded_pem_data = f.read()

        if loaded_pem_data:

            SIGN_PRIVATE_KEY = serialization.load_pem_private_key(
                loaded_pem_data,
                password=bytes(USER_PASSWORD)
            )

            SIGN_PUBLIC_KEY = SIGN_PRIVATE_KEY.public_key()

            return


    # ... генерация

    SIGN_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
    SIGN_PUBLIC_KEY = SIGN_PRIVATE_KEY.public_key()

    # Сохранение приватного ключа в файл в зашифрованном виде

    pem_private_data = SIGN_PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(bytes(USER_PASSWORD))
    )

    # Записываем байты в файл
    with open(SIGN_PRIVATE_FILE_PATH, "wb") as f:
        f.write(pem_private_data)


# Проверка существования цифровой подписи собеседника и ее получение
def check_and_get_companion_sign():

    global COMPANION_SIGN

    COMPANION_SIGN_FILE_PATH = os.path.join(COMPANION_NODE_ID, KNOWN_NODES_DIR_PATH)

    # цифровая подпись существует
    # достаем из файла и расшифровываем ее
    if os.path.exists(COMPANION_SIGN_FILE_PATH):

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
        time.sleep(5)

        # если собеседник не отправил свою подпись, то значит та которая в файле - актуальна
        if not COMPANION_SIGN:
            COMPANION_SIGN = loaded_public_key
            return

        # если не существует то мы отправляем собеседнику свою подпись, а он в ответ должен отправить свою подпись.
        # далее уже происходит проверка подписей

    else:

        sign_public_bytes_X962 = SIGN_PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )

        SENDER.send_sign(sign_public_bytes_X962)

    # Если код продолжается, то значит что новая подпись пришла или же подписи просто нет в файле, и нужно получить новую подпись от собеседника и записать ее в файл

    while not COMPANION_SIGN:
        print_formatted_text(HTML(f'<ansiyellow>Waiting companion signature...</ansiyellow>\n'))
        time.sleep(5)


    # Вывод подписи пользователя
    print_formatted_text(HTML(f'<ansiyellow>Your signature. Show this to companion:\n{get_firts_last_4_chars_sign(SIGN_PUBLIC_KEY)}</ansiyellow>\n'))
    # Проверка подписи собеседника пользователем
    if answer(f"Is the companion signature correct?\n{get_firts_last_4_chars_sign(COMPANION_SIGN)}"):

        # Доверяем, записываем, используем эту подпись

        # Зашифровываем публичную подпись собеседника паролем

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
        raise TypeError("do not trust the signature")


# Генерация и обмен публичными ключами
def generate_and_exchange_ecc_keys():

    # Генерация пары ключей
    MY_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
    my_public_key = MY_PRIVATE_KEY.public_key()
    my_pkey_bytes = my_public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )

    # Передача публичного ключа
    SENDER.send_public_key(my_pkey_bytes)

    # Ожидаем публичный ключ от собеседника
    while not COMPANION_PUBLIC_KEY:
        print_formatted_text(HTML(f'<ansiyellow>Waiting companion public key...</ansiyellow>\n'))
        time.sleep(5)

    print("okey")

    # Вычисление симетричного ключа



# Принимает готовые данные от Listener
# а именно PayloadPacket
def ready_data_ingester(pack_type, payload_packet: packet.PayloadPacket):

    global COMPANION_NODE_ID
    global COMPANION_SIGN
    global COMPANION_PUBLIC_KEY

    if pack_type == packet.PackTypes.SERVICE.value:

        # print(packet.CMDTypes(payload_packet.pack_type).name)
        # print(payload_packet.payload)

        if payload_packet.pack_type == packet.CMDTypes.MY_NODE_ID.value:
            COMPANION_NODE_ID = payload_packet.payload.decode()

        if payload_packet.pack_type == packet.CMDTypes.MY_SIGN.value:
            # print("Listener: new COMPANION_SIGN")
            COMPANION_SIGN = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(),
                payload_packet.payload
            )

        if payload_packet.pack_type == packet.CMDTypes.MY_PUBLIC_KEY.value:
            COMPANION_PUBLIC_KEY = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(),
                payload_packet.payload
            )

        # если получили node_id и подпись, то DO_SIGN = True
        # если получили public_key, то DO_ENCRYPT = True


    elif pack_type == packet.PackTypes.COMMUNIC.value:

        if payload_packet.pack_type == packet.DataTypes.TEXT.value:

            with patch_stdout():
                print_formatted_text(HTML(f'<ansiblue>peer:</ansiblue> {payload_packet.payload.decode()}'))

        else:
            print("Not TEXT data type:\n", payload_packet.payload)


def remove_password_from_ram():
    for i in range(len(USER_PASSWORD)):
        USER_PASSWORD[i] = 0







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
