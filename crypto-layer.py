import threading
import sys
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text


session = PromptSession()


def main():

    listener_thread = threading.Thread(target=listener)
    listener_thread.start()

    sender()


def sender():

    while True:

        with patch_stdout():
            user_input = session.prompt(HTML('<ansigreen>you></ansigreen> ')).strip()

        if user_input == ":":
            if not answer("<ansired>You want send this?</ansired>"):
                sender_console()
                continue


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
            print_formatted_text(HTML('<ansired>Unknown command!</ansired>'))


def listener():
    msg = "Hello, how are you?"
    while True:
        with patch_stdout():
            print_formatted_text(HTML('<ansiblue>peer:</ansiblue> Hello'))
        time.sleep(5)


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


if __name__ == "__main__":
    main()
