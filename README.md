# Итоговый проект. Платформа для отслеживания и симуляции торговли валютами

Консольное приложение для симуляции торговли фиатными и криптовалютами, реализованное на Python

## Установка
Для установки, убедитесь, что у вас установлен Python и Poetry, а затем склонируйте репозиторий с помощью команды:
git clone https://github.com/Seeneld/finalproject_priezzhikh_timofey_M25-555.git

Затем перейдите в папку проекта:
cd finalproject_priezzhikh_timofey_M25-555

Перейдите на сайт https://www.exchangerate-api.com/, зарегистрируйтесь и получите персональный API-ключ.

Этот ключ используйте далее

Установите зависимости и запустите проект:

export EXCHANGERATE_API_KEY="ваш ключ" (кавычки убрать)

make install
make project


## Доступные команды:

help                                                (вывод справки)
register --username <имя> --password <пароль>       (регистрация пользователя)
login --username <имя> --password <пароль>          (авторизация пользователя)
show-portfolio --base <валюта>                      (портфолио пользователя)
buy --currency <валюта> --amount <количество>       (купить валюту)
sell --currency <валюта> --amount <количество>      (продать валюту)
get-rate --from <валюта> --to <валюта>              (курс обмена валют)
update-rates --source <источник>                    (обновить курсы обмена валют)
show-rates --currency <валюта> --top <количество>   (курс валют в USD)
exit                                                (выход из приложения)

Команды show-portfolio, buy, sell доступны только авторизованным пользователям
Для команд show-portfolio, update-rates, show-rates аргументы указываются опционально