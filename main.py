import pandas as pd
from config import main_directory
from models import *
from art import text2art
from termcolor import colored
import inquirer
from inquirer.themes import load_theme_from_dict as loadth

lst_futures_obj = []


def get_action(choices_lst: list) -> str:
    theme = {
        "Question": {
            "brackets_color": "bright_yellow"
        },
        "List": {
            "selection_color": "bright_yellow"
        }
    }

    question = [
        inquirer.List(
            "action",
            message=colored("Выберите действие", 'light_yellow'),
            choices=choices_lst
        )
    ]
    return inquirer.prompt(question, theme=loadth(theme))['action']


def add_console():
    f = FuturesObj()
    f.read_console()
    lst_futures_obj.append(f)


def add_file():
    df = pd.read_csv(f'{main_directory}/data.csv')
    for i in range(len(df)):
        f = FuturesObj()
        f.read_csv(df, i)
        lst_futures_obj.append(f)


def clear_lst():
    lst_futures_obj.clear()


def show_list():
    separator = "-" * 15
    for i in lst_futures_obj:
        print(f'{separator}\n'
              f'{i}'
              f'{separator}\n')


def main():
    print('Starting bot. The output appears when opening and closing positions')

    def check_position_thread(item):
        attempts = 0
        while attempts < 5:
            try:
                check_position(item, False)
                break
            except Exception as e:
                print(f'Error: {e} New connection attempt {item.symbol}')
                attempts += 1
                time.sleep(15)
        if attempts == 5:
            print(f'Failed to restore connection for {item.symbol}. Close position')

    def console_command_thread():
        stopped = 0
        while stopped < len(threads_dict):
            command = input().split()
            if command[0] == 'stop' and command[1] in threads_dict:
                threads_dict[command[1]].stop()
                print(f'stopped {command[1]}')
                stopped += 1
            if command[0] == 'exit':
                for thread_name in threads_dict:
                    if not threads_dict[thread_name].stopped():
                        threads_dict[thread_name].stop()
                        print(f'stopped {command[1]}')
                        stopped += 1

    for item in lst_futures_obj:
        threads_dict[item.symbol] = StoppableThread(target=check_position_thread, args=(item,))
        threads_dict[item.symbol].start()

    console_thread = threading.Thread(target=console_command_thread)
    console_thread.start()

    for thread in threads_dict.values():
        thread.join()

    console_thread.join()


if __name__ == '__main__':
    art = text2art(text="Binance    Futures     bot", font="standart")
    print(colored(art, 'light_magenta'))

    while True:
        choice_dict = {
            'Добавить новую пару': add_console,
            'Добавить пары с файла': add_file,
            'Удалить все пары': clear_lst,
            'Посмотреть список пар': show_list,
            'Запустить': main,
        }

        action = get_action(list(choice_dict.keys()))
        if action in choice_dict:
            choice_dict[action]()
            print()
