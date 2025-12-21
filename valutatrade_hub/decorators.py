import logging
import functools
from typing import Any, Callable
from datetime import datetime

from valutatrade_hub.core.exceptions import UserError


logger = logging.getLogger("valutatrade")

def log_action(action_name: str, verbose: bool = False) -> Callable:
    """Декоратор для логирования ключевых операций"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Извлечение контекста
            username = "unknown"
            user_id = None
            currency_code = "N/A"
            amount = None
            base_currency = "USD"
            rate = None

            # Попытка извлечь данные из аргументов и результата
            try:
                usecase_instance = args[0] if args else None
                if hasattr(usecase_instance, 'get_logged_in_user'):
                    try:
                        user = usecase_instance.get_logged_in_user()
                        username = user.username
                        user_id = user.user_id
                    except (UserError, AttributeError):
                        username = "unauthenticated"

                # Извлечение параметров из kwargs или args
                if 'currency' in kwargs:
                    currency_code = kwargs['currency']
                elif len(args) >= 2 and isinstance(args[1], str):
                    currency_code = args[1]

                if 'amount' in kwargs:
                    amount = kwargs['amount']
                elif len(args) >= 3 and isinstance(args[2], (int, float)):
                    amount = args[2]

                if 'base' in kwargs:
                    base_currency = kwargs['base']

                # Для get-rate
                if 'from_curr' in kwargs:
                    currency_code = f"{kwargs['from_curr']}->{kwargs['to_curr']}"

            except Exception:
                pass

            result_status = "ERROR"
            error_message = None
            error_type = None

            try:
                result = func(*args, **kwargs)
                result_status = "OK"
                if verbose and isinstance(result, str):
                    pass
                return result
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                raise
            finally:
                # Формирование логов
                log_parts = [
                    action_name,
                    f"user='{username}'",
                ]
                if user_id is not None:
                    log_parts.append(f"user_id={user_id}")
                if currency_code != "N/A":
                    log_parts.append(f"currency='{currency_code}'")
                if amount is not None:
                    log_parts.append(f"amount={amount:.4f}")
                if rate is not None:
                    log_parts.append(f"rate={rate:.2f}")
                if base_currency:
                    log_parts.append(f"base='{base_currency}'")
                log_parts.append(f"result={result_status}")
                if error_message:
                    log_parts.append(f"error_type={error_type}")
                    log_parts.append(f"error_message='{error_message}'")

                log_message = " ".join(log_parts)
                logger.info(log_message)

        return wrapper
    return decorator