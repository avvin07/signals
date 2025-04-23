# Trading Analysis Script

[![CI](https://github.com/yourusername/your-repo-name/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/your-repo-name/actions)
[![Coverage Status](https://coveralls.io/repos/github/yourusername/your-repo-name/badge.svg?branch=main)](https://coveralls.io/github/yourusername/your-repo-name?branch=main)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Описание проекта

`trading_analysis.py` — скрипт для анализа и визуализации торговых сигналов по парам ETH-USDT и BTC-USDT. Скрипт:
- Загружает и подготавливает данные из CSV/TXT-файла с полями <DATE>, <TIME>, цены закрытия и торговых сигналов
- Определяет периоды открытия и закрытия длинных и коротких позиций
- Рассчитывает метрики сделок: % прибыли/убытка, изменения депозита, продолжительность сделки
- Формирует статистику по всем сделкам и текущей открытой позиции
- Строит график цен с нанесёнными сигналами, подсветкой зон позиции и выводом статистики
- Сохраняет итоговый график в PNG-файл

## Особенности

- Поддержка двух инструментов: ETH-USDT и BTC-USDT
- Автоматический выбор нужных столбцов для каждого символа
- Расчёт нереализованного P/L для открытой позиции
- Подсветка фона для периодов long (зелёный) и short (красный)
- Параметры запуска через CLI с дефолтными настройками в `config.py`

## Установка и требования

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Создать виртуальное окружение и установить зависимости:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/Mac
   venv\Scripts\activate         # Windows PowerShell
   pip install --upgrade pip
   pip install pandas numpy matplotlib seaborn
   ```

3. (Опционально) Создать файл `config.py` рядом со скриптом и задать параметры по умолчанию:
   ```python
   # config.py
   DEFAULT_DATA_PATH = 'ETH-USDT-SWAP_5M.txt'
   FIGURE_SIZE = (20, 16)
   DPI = 300
   OUTPUT_FILE = 'trading_signals.png'
   ```

## Использование скрипта

Запуск без аргументов (используются значения из `config.py`):
```bash
python trading_analysis.py
```

Запуск с указанием пути к файлу данных и параметров вывода:
```bash
python trading_analysis.py \
  --file "путь/к/данным.txt" \
  --output "результат.png" \
  --dpi 300
```

### Доступные опции

- `-f, --file`: путь к файлу с данными (по умолчанию задаётся в `config.py`)
- `-o, --output`: путь для сохранения итогового графика (по умолчанию задаётся в `config.py`)
- `--dpi`: разрешение выходного изображения в DPI (по умолчанию задаётся в `config.py`)

## Формат входных данных

Исходный файл должен содержать следующие колонки (имена без угловых скобок):

| Колонка                | Описание                                      |
|------------------------|-----------------------------------------------|
| DATE                   | Дата в формате `YYYYMMDD`                     |
| TIME                   | Время в формате `HHMMSS`                      |
| CLOSE                  | Цена закрытия ETH-USDT                        |
| CLOSEBTC               | Цена закрытия BTC-USDT                        |
| LOTSFACT               | Объём сделки ETH в лотах                      |
| LOT_BTCUSDT            | Объём сделки BTC в лотах                      |
| SIGNAL_LONG            | Сигнал открытия длинной позиции ETH           |
| SIGNAL_CLOSELONG       | Сигнал закрытия длинной позиции ETH           |
| SIGNALSHORT            | Сигнал открытия короткой позиции ETH          |
| SIGNALCLOSESHORT       | Сигнал закрытия короткой позиции ETH          |
| SIGNALLONGBTCUSDT      | Сигнал открытия длинной позиции BTC           |
| SIGNALCLOSELONGBTCUSDT | Сигнал закрытия длинной позиции BTC           |
| SIGNALSHORTBTCUSDT     | Сигнал открытия короткой позиции BTC          |
| SIGNALCLOSESHORTBTCUSDT| Сигнал закрытия короткой позиции BTC          |
| DEPO                   | Текущий депозит (баланс) в USDT               |

## Основные функции скрипта

- `load_and_prepare_data(file_path)` — загрузка CSV/TXT, приведение колонок, установка индекса `datetime`
- `find_position_periods(df, symbol)` — поиск периодов сделок по сигналам
- `calculate_trade_metrics(...)` — расчёт прибыли/убытка, % изменения депозита, длительности сделки
- `get_current_position_info(df, last_row, symbol)` — информация по текущей позиции и нереализованному P/L
- `analyze_trades(df, symbol)` — сбор всех сделок, вычисление статистики и просадки
- `format_trade_statistics(trades_stats)` — форматирование статистики в текст для вывода на графике
- `plot_trading_signals(df, ax, symbol)` — построение графика цены, сделок и статистики
- `main()` — точка входа: парсинг аргументов, загрузка данных, построение и сохранение графиков

## Пример использования

```bash
python trading_analysis.py -f data/ETH-USDT-SWAP_5M.txt -o out/eth_btc_signals.png --dpi 400
```

## Скриншоты

![Пример графика ETH]([/main/trading_signals.png])
*График цен ETH-USDT с торговыми сигналами и статистикой*


## Структура репозитория

```
trading_analysis/
├── trading_analysis.py    # Основной скрипт анализа и визуализации
├── config.py              # Конфигурационный файл с настройками по умолчанию
├── requirements.txt       # Зависимости проекта
├── README.md              # Документация проекта
├── LICENSE                # Лицензия проекта
├── data/                  # Каталог с исходными данными
└── output/                # Каталог для сохраненных графиков и результатов
```

## Масштабирование: добавление новых инструментов

Чтобы добавить поддержку нового торгового инструмента (например, XRP-USDT):
1. Убедитесь, что в файле данных присутствуют колонки `CLOSE<Symbol>`, `LOT_<Symbol>`, и соответствующие сигналы `SIGNAL...<Symbol>`.
2. В функциях `analyze_trades`, `get_current_position_info` и `find_position_periods` добавьте ветку `elif symbol == '<SYMBOL>'` с новыми именами столбцов.
3. При необходимости расширьте CLI-парсер аргументов для параметра `--symbol`.
4. Проведите тестовый запуск для нового инструмента.

## FAQ

**В: Почему не отображается маркер текущей позиции?**  
Убедитесь, что сигналы входа/выхода корректны и вы передаете правильный `symbol` при запуске.

**В: Как изменить шрифт в статистике на графике?**  
Параметр `fontsize` задается в функции `format_trade_statistics`.

**В: Получаю `FileNotFoundError` при загрузке данных.**  
Проверьте путь к файлу через `--file` и убедитесь, что файл находится в указанной директории.

**В: Как интегрировать скрипт в свой проект?**  
См. пример кода ниже.

## Пример импорта и использования

```python
from trading_analysis import load_and_prepare_data, analyze_trades, plot_trading_signals
import matplotlib.pyplot as plt

df = load_and_prepare_data('ETH-USDT-SWAP_5M.txt')
stats, _ = analyze_trades(df, symbol='ETH')

fig, ax = plt.subplots(figsize=(12, 6))
plot_trading_signals(df, ax, symbol='ETH')
plt.show()
```

## Контрибьюции

PR приветствуются! Пожалуйста, создавайте issue или форк и отправляйте pull request.

## Лицензия

MIT License. Смотрите файл `LICENSE` для подробнее информации. 
