import shlex

from valutatrade_hub.core.usecases import UseCases, UserError


# Глобальный экземпляр бизнес-логики
_usecases = UseCases(
    users_file='data/users.json',
    portfolios_file='data/portfolios.json',
    rates_file='data/rates.json'
)


def print_help_message() -> None:
    """Печать справки по командам"""
    help_text = """Доступные команды:

help
register --username <имя> --password <пароль>
login --username <имя> --password <пароль>
show-portfolio [--base <валюта>]
buy --currency <код> --amount <количество>
sell --currency <код> --amount <количество>
get-rate --from <валюта> --to <валюта>
exit
"""
    print(help_text.strip())


def parse_args(raw_input: str) -> dict:
    """Безопасный парсинг строки команды в структуру аргументов"""
    try:
        parts = shlex.split(raw_input)
    except ValueError as e:
        raise UserError(f"Ошибка парсинга команды: {e}")

    if not parts:
        raise UserError("Пустая команда")

    command = parts[0]
    args = {}
    i = 1
    while i < len(parts):
        part = parts[i]
        if part.startswith("--") and i + 1 < len(parts):
            key = part[2:]
            value = parts[i + 1]
            args[key] = value
            i += 2
        else:
            raise UserError(f"Некорректный аргумент: {part}")
    return {"command": command, "args": args}


def run_cli() -> None:
    """Запуск основного цикла командной строки"""
    print_help_message()
    print()

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input == "exit":
                print("Выход")
                break

            if user_input == "help":
                print_help_message()
                print()
                continue

            parsed = parse_args(user_input)
            command = parsed["command"]
            args = parsed["args"]

            if command == "register":
                username = args.get("username")
                password = args.get("password")
                if not username or not password:
                    raise UserError("Требуются аргументы --username и --password")
                message = _usecases.register_user(username, password)
                print(message)

            elif command == "login":
                username = args.get("username")
                password = args.get("password")
                if not username or not password:
                    raise UserError("Требуются аргументы --username и --password")
                message = _usecases.login_user(username, password)
                print(message)

            elif command == "show-portfolio":
                base = args.get("base", "USD")
                message = _usecases.show_portfolio(base)
                print(message)

            elif command == "buy":
                currency = args.get("currency")
                amount_str = args.get("amount")
                if not currency or not amount_str:
                    raise UserError("Требуются --currency и --amount")
                try:
                    amount = float(amount_str)
                except ValueError:
                    raise UserError("'amount' должен быть числом")
                if amount <= 0:
                    raise UserError("'amount' должен быть положительным числом")
                message = _usecases.buy_currency(currency, amount)
                print(message)

            elif command == "sell":
                currency = args.get("currency")
                amount_str = args.get("amount")
                if not currency or not amount_str:
                    raise UserError("Требуются --currency и --amount")
                try:
                    amount = float(amount_str)
                except ValueError:
                    raise UserError("'amount' должен быть числом")
                if amount <= 0:
                    raise UserError("'amount' должен быть положительным числом")
                message = _usecases.sell_currency(currency, amount)
                print(message)

            elif command == "get-rate":
                from_curr = args.get("from")
                to_curr = args.get("to")
                if not from_curr or not to_curr:
                    raise UserError("Требуются --from и --to")
                message = _usecases.get_exchange_rate(from_curr, to_curr)
                print(message)

            else:
                print(f"Неизвестная команда: {command}. Введите 'help'.")

        except UserError as e:
            print(f"Ошибка: {e}")
        except KeyboardInterrupt:
            print("\nВыход")
            break
        except Exception as e:
            print(f"Внутренняя ошибка: {e}")