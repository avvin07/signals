import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import argparse

# Настройка стиля графиков
plt.style.use('default')  # Используем стандартный стиль matplotlib
sns.set_theme()  # Применяем базовую тему seaborn

def load_and_prepare_data(file_path):
    """
    Загрузка и подготовка данных из файла
    """
    try:
        # Пробуем разные кодировки
        encodings = ['utf-16', 'utf-16le', 'utf-16be', 'latin1', 'cp1251']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Данные успешно загружены с кодировкой {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Ошибка при попытке чтения с кодировкой {encoding}: {str(e)}")
                continue
        
        if df is None:
            raise ValueError("Не удалось прочитать файл ни с одной из доступных кодировок")
        
        # Исправление имен столбцов (удаление угловых скобок)
        df.columns = [col.strip('<>') for col in df.columns]
        
        # Вывод информации о столбцах
        print("\nСписок столбцов в файле:")
        for col in df.columns:
            print(f"- {col}")
        
        # Создание временного индекса
        df['datetime'] = pd.to_datetime(df['DATE'].astype(str) + ' ' + 
                                      df['TIME'].astype(str).str.zfill(6),
                                      format='%Y%m%d %H%M%S')
        df.set_index('datetime', inplace=True)
        
        print(f"\nЗагружено {len(df)} строк данных")
        
        # Проверка наличия необходимых столбцов
        required_columns = ['CLOSE', 'SIGNAL_LONG', 'SIGNAL_CLOSELONG', 'SIGNALSHORT', 'SIGNALCLOSESHORT']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print("\nВНИМАНИЕ: Отсутствуют следующие столбцы:")
            for col in missing_columns:
                print(f"- {col}")
        
        return df
        
    except Exception as e:
        print(f"Ошибка при загрузке данных: {str(e)}")
        raise

def find_position_periods(df, symbol='ETH'):
    """
    Находит периоды нахождения в позициях
    """
    long_periods = []
    short_periods = []
    
    # Определяем имена столбцов в зависимости от символа
    if symbol == 'BTC':
        long_signal = 'SIGNALLONGBTCUSDT'
        long_close = 'SIGNALCLOSELONGBTCUSDT'
        short_signal = 'SIGNALSHORTBTCUSDT'
        short_close = 'SIGNALCLOSESHORTBTCUSDT'
    else:
        long_signal = 'SIGNAL_LONG'
        long_close = 'SIGNAL_CLOSELONG'
        short_signal = 'SIGNALSHORT'
        short_close = 'SIGNALCLOSESHORT'
    
    price_col = 'CLOSE'  # Всегда используем CLOSE для обоих инструментов
    
    # Находим периоды длинных позиций
    try:
        long_entries = df[df[long_signal] == 1].index
        long_exits = df[df[long_close] == 1].index
        
        if len(long_entries) > 0 and len(long_exits) > 0:
            for entry in long_entries:
                exits_after = long_exits[long_exits > entry]
                if len(exits_after) > 0:
                    long_periods.append((entry, exits_after[0]))
        
        # Находим периоды коротких позиций
        short_entries = df[df[short_signal] == 1].index
        short_exits = df[df[short_close] == 1].index
        
        if len(short_entries) > 0 and len(short_exits) > 0:
            for entry in short_entries:
                exits_after = short_exits[short_exits > entry]
                if len(exits_after) > 0:
                    short_periods.append((entry, exits_after[0]))
    except KeyError as e:
        print(f"Ошибка: Отсутствует столбец {str(e)} для {symbol}")
        raise
    
    return long_periods, short_periods, price_col

def calculate_trade_metrics(df, entry_time, exit_time, entry_price, exit_price, depo_start, depo_end, trade_type='LONG'):
    """
    Расчет метрик для сделки
    """
    if trade_type == 'LONG':
        profit_pct = (exit_price - entry_price) / entry_price * 100
    else:  # SHORT
        profit_pct = (entry_price - exit_price) / entry_price * 100
        
    depo_change_pct = (depo_end - depo_start) / depo_start * 100
    duration = (exit_time - entry_time).total_seconds() / 60  # в минутах
    return profit_pct, depo_change_pct, duration

def get_current_position_info(df, last_row, symbol='ETH'):
    """
    Получение информации о текущей позиции
    """
    if symbol == 'BTC':
        long_signal = 'SIGNALLONGBTCUSDT'
        long_close = 'SIGNALCLOSELONGBTCUSDT'
        short_signal = 'SIGNALSHORTBTCUSDT'
        short_close = 'SIGNALCLOSESHORTBTCUSDT'
        price_col = 'CLOSEBTC'
        lots_col = 'LOT_BTCUSDT'
    else:
        long_signal = 'SIGNAL_LONG'
        long_close = 'SIGNAL_CLOSELONG'
        short_signal = 'SIGNALSHORT'
        short_close = 'SIGNALCLOSESHORT'
        price_col = 'CLOSE'
        lots_col = 'LOTSFACT'
    
    # Находим последние сигналы
    last_long_entry = df[df[long_signal] == 1].index[-1] if any(df[long_signal] == 1) else None
    last_long_exit = df[df[long_close] == 1].index[-1] if any(df[long_close] == 1) else None
    last_short_entry = df[df[short_signal] == 1].index[-1] if any(df[short_signal] == 1) else None
    last_short_exit = df[df[short_close] == 1].index[-1] if any(df[short_close] == 1) else None
    
    current_position = None
    entry_time = None
    entry_price = None
    current_price = last_row[price_col]
    current_profit = 0
    lots = float(last_row[lots_col])
    depo = float(last_row['DEPO'])
    
    # Проверяем наличие открытой длинной позиции
    if last_long_entry is not None and (last_long_exit is None or last_long_entry > last_long_exit):
        current_position = 'LONG'
        entry_time = last_long_entry
        entry_price = df.loc[last_long_entry, price_col]
        current_profit = ((current_price - entry_price) / entry_price) * 100
        unrealized_pnl = lots * (current_price - entry_price)
        unrealized_pnl_pct = (unrealized_pnl / depo) * 100 if depo != 0 else 0
    
    # Проверяем наличие открытой короткой позиции
    elif last_short_entry is not None and (last_short_exit is None or last_short_entry > last_short_exit):
        current_position = 'SHORT'
        entry_time = last_short_entry
        entry_price = df.loc[last_short_entry, price_col]
        current_profit = ((entry_price - current_price) / entry_price) * 100
        unrealized_pnl = lots * (entry_price - current_price)
        unrealized_pnl_pct = (unrealized_pnl / depo) * 100 if depo != 0 else 0
    else:
        unrealized_pnl = 0
        unrealized_pnl_pct = 0
        lots = 0
    
    amount = abs(lots * current_price) if lots != 0 else 0
    depo_usage_pct = (amount / depo) * 100 if depo != 0 else 0
    
    return {
        'position': current_position,
        'entry_time': entry_time,
        'entry_price': entry_price,
        'current_price': current_price,
        'current_profit': current_profit,
        'lots': abs(lots),
        'price': current_price,
        'amount': amount,
        'depo_usage_pct': depo_usage_pct,
        'unrealized_pnl': unrealized_pnl,
        'unrealized_pnl_pct': unrealized_pnl_pct
    }

def analyze_trades(df, symbol='ETH'):
    """
    Анализ сделок и расчет статистики
    """
    print(f"\nАнализ сделок для {symbol}-USDT...")
    
    trades_stats = {
        'long_trades': [], 
        'short_trades': [],
        'max_depo_drawdown': 0
    }
    
    # Определяем имена столбцов в зависимости от символа
    if symbol == 'BTC':
        long_signal = 'SIGNALLONGBTCUSDT'
        long_close = 'SIGNALCLOSELONGBTCUSDT'
        short_signal = 'SIGNALSHORTBTCUSDT'
        short_close = 'SIGNALCLOSESHORTBTCUSDT'
        price_col = 'CLOSEBTC'  # Используем CLOSEBTC для BTC
    else:
        long_signal = 'SIGNAL_LONG'
        long_close = 'SIGNAL_CLOSELONG'
        short_signal = 'SIGNALSHORT'
        short_close = 'SIGNALCLOSESHORT'
        price_col = 'CLOSE'
    
    print(f"Используется столбец цены: {price_col}")
    
    # Анализ длинных позиций
    long_entries = df[df[long_signal] == 1].index
    long_exits = df[df[long_close] == 1].index
    
    for entry in long_entries:
        exits_after = long_exits[long_exits > entry]
        if len(exits_after) > 0:
            exit_time = exits_after[0]
            entry_price = df.loc[entry, price_col]
            exit_price = df.loc[exit_time, price_col]
            depo_start = df.loc[entry, 'DEPO']
            depo_end = df.loc[exit_time, 'DEPO']
            
            profit_pct, depo_change_pct, duration = calculate_trade_metrics(
                df, entry, exit_time, entry_price, exit_price, depo_start, depo_end, 'LONG'
            )
            
            trades_stats['long_trades'].append({
                'entry_time': entry,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'depo_change_pct': depo_change_pct,
                'duration': duration
            })
    
    # Анализ коротких позиций
    short_entries = df[df[short_signal] == 1].index
    short_exits = df[df[short_close] == 1].index
    
    for entry in short_entries:
        exits_after = short_exits[short_exits > entry]
        if len(exits_after) > 0:
            exit_time = exits_after[0]
            entry_price = df.loc[entry, price_col]
            exit_price = df.loc[exit_time, price_col]
            depo_start = df.loc[entry, 'DEPO']
            depo_end = df.loc[exit_time, 'DEPO']
            
            profit_pct, depo_change_pct, duration = calculate_trade_metrics(
                df, entry, exit_time, entry_price, exit_price, depo_start, depo_end, 'SHORT'
            )
            
            trades_stats['short_trades'].append({
                'entry_time': entry,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'depo_change_pct': depo_change_pct,
                'duration': duration
            })
    
    # Расчет общей статистики
    all_trades = trades_stats['long_trades'] + trades_stats['short_trades']
    if all_trades:
        # Расчет просадки по депозиту
        depo_changes = [trade['depo_change_pct'] for trade in all_trades]
        cumulative_depo = np.cumsum(depo_changes)
        trades_stats['max_depo_drawdown'] = min(0, np.min(cumulative_depo))
    
    # Получение информации о текущей позиции
    trades_stats['current_position'] = get_current_position_info(df, df.iloc[-1], symbol)
    
    return trades_stats, price_col

def format_trade_statistics(trades_stats):
    """
    Форматирование статистики сделок для вывода на график
    """
    long_trades = trades_stats['long_trades']
    short_trades = trades_stats['short_trades']
    current_pos = trades_stats['current_position']
    
    # Расчет статистики для длинных позиций
    long_profits = [trade['depo_change_pct'] for trade in long_trades]
    long_profitable = sum(1 for p in long_profits if p > 0)
    
    # Расчет статистики для коротких позиций
    short_profits = [trade['depo_change_pct'] for trade in short_trades]
    short_profitable = sum(1 for p in short_profits if p > 0)
    
    # Общая статистика
    all_profits = long_profits + short_profits
    total_profit = sum(all_profits)
    
    stats_text = [
        'Статистика сделок:',
        f'Всего сделок: {len(all_profits)}',
        f'Суммарный P/L: {total_profit:.2f}%',
        '',
        'Длинные позиции:',
        f'Количество: {len(long_profits)}',
        f'Прибыльных: {long_profitable}',
        f'Убыточных: {len(long_profits) - long_profitable}',
        f'Средний P/L: {np.mean(long_profits):.2f}%' if long_profits else 'Нет сделок',
        f'Макс. прибыль: {max(long_profits):.2f}%' if long_profits else 'Нет сделок',
        f'Макс. убыток: {min(long_profits):.2f}%' if long_profits else 'Нет сделок',
        '',
        'Короткие позиции:',
        f'Количество: {len(short_profits)}',
        f'Прибыльных: {short_profitable}',
        f'Убыточных: {len(short_profits) - short_profitable}',
        f'Средний P/L: {np.mean(short_profits):.2f}%' if short_profits else 'Нет сделок',
        f'Макс. прибыль: {max(short_profits):.2f}%' if short_profits else 'Нет сделок',
        f'Макс. убыток: {min(short_profits):.2f}%' if short_profits else 'Нет сделок',
        '',
        f'Макс. просадка по депозиту: {trades_stats["max_depo_drawdown"]:.2f}%',
        '',
        'Текущая позиция:',
        f'Тип: {current_pos["position"]}',
        f'Количество лотов: {current_pos["lots"]:.4f}',
        f'Цена: {current_pos["price"]:.2f}',
        f'Сумма: {current_pos["amount"]:.2f}',
        f'Процент капитала: {current_pos["depo_usage_pct"]:.2f}%',
        f'Нереализованный P/L: {current_pos["unrealized_pnl"]:.2f}',
        f'Нереализованный P/L%: {current_pos["unrealized_pnl_pct"]:.2f}%'
    ]
    
    return '\n'.join(stats_text)

def plot_trading_signals(df, ax, symbol='ETH'):
    """
    Построение графика цены с сигналами
    """
    try:
        print(f"\nПостроение графика {symbol}-USDT...")
        
        # Анализ сделок
        trades_stats, price_col = analyze_trades(df, symbol)
        
        print("Отрисовка графика цены...")
        # Построение графика цены закрытия
        ax.plot(df.index, df[price_col], label=f'{symbol}-USDT Price', color='blue', alpha=0.7, linewidth=1)
        
        print("Отрисовка сделок и позиций...")
        # Подсветка фона в зависимости от позиции
        lots_col = 'LOT_BTCUSDT' if symbol == 'BTC' else 'LOTSFACT'
        
        # Создаем массив для хранения цветов фона
        background_colors = []
        positions = []
        
        # Определяем цвет для каждого интервала
        for i in range(len(df)):
            lots = float(df.iloc[i][lots_col])
            if abs(lots) > 0.000001:  # Если есть открытая позиция
                if lots > 0:  # Long position
                    background_colors.append('lightgreen')
                    positions.append('long')
                else:  # Short position
                    background_colors.append('lightpink')
                    positions.append('short')
            else:
                background_colors.append('none')
                positions.append('none')
        
        # Отрисовка фона
        for i in range(len(df)-1):
            if background_colors[i] != 'none':
                ax.axvspan(df.index[i], df.index[i+1], color=background_colors[i], alpha=0.1)
        
        # Отрисовка сделок
        for trade in trades_stats['long_trades']:
            # Точка входа
            ax.scatter(trade['entry_time'], trade['entry_price'],
                      color='limegreen', marker='^', s=80,
                      label='Long Entry' if trade == trades_stats['long_trades'][0] else "",
                      zorder=5)
            # Линия до точки выхода
            ax.plot([trade['entry_time'], trade['exit_time']],
                   [trade['entry_price'], trade['exit_price']],
                   color='green', linestyle=':', alpha=0.5, linewidth=1)
        
        for trade in trades_stats['short_trades']:
            # Точка входа
            ax.scatter(trade['entry_time'], trade['entry_price'],
                      color='red', marker='v', s=80,
                      label='Short Entry' if trade == trades_stats['short_trades'][0] else "",
                      zorder=5)
            # Линия до точки выхода
            ax.plot([trade['entry_time'], trade['exit_time']],
                   [trade['entry_price'], trade['exit_price']],
                   color='red', linestyle=':', alpha=0.5, linewidth=1)
        
        # Добавляем маркер для текущей открытой позиции
        current_pos = trades_stats['current_position']
        if current_pos['position'] is not None:  # Изменено условие проверки
            if current_pos['position'] == 'LONG':
                ax.scatter(current_pos['entry_time'], current_pos['entry_price'],  # Используем время и цену входа
                          color='limegreen', marker='^', s=120,
                          label='Current Long Position', zorder=5,
                          edgecolor='darkgreen', linewidth=2)
            elif current_pos['position'] == 'SHORT':
                ax.scatter(current_pos['entry_time'], current_pos['entry_price'],  # Используем время и цену входа
                          color='red', marker='v', s=120,
                          label='Current Short Position', zorder=5,
                          edgecolor='darkred', linewidth=2)
        
        print("Настройка оформления графика...")
        # Настройка графика
        ax.set_title(f'{symbol}-USDT', fontsize=14, pad=10)  # Упрощенное название графика
        ax.set_xlabel('Время', fontsize=12)
        ax.set_ylabel('Цена', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(axis='x', rotation=45)
        
        # Добавляем статистику справа от графика
        stats_text = format_trade_statistics(trades_stats)
        ax.text(1.02, 0.98, stats_text,
                transform=ax.transAxes,
                verticalalignment='top',
                fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Настройка легенды
        ax.legend(loc='upper left')
        
    except Exception as e:
        print(f"Ошибка при построении графика для {symbol}: {str(e)}")
        raise

def main():
    try:
        import sys
        import os
        from config import DEFAULT_DATA_PATH, FIGURE_SIZE, DPI, OUTPUT_FILE
        
        # Настройка парсера аргументов командной строки
        parser = argparse.ArgumentParser(description='Анализ торговых сигналов')
        parser.add_argument('--file', '-f', type=str, default=DEFAULT_DATA_PATH,
                          help='Путь к файлу с данными (по умолчанию: %(default)s)')
        parser.add_argument('--output', '-o', type=str, default=OUTPUT_FILE,
                          help='Путь для сохранения графика (по умолчанию: %(default)s)')
        parser.add_argument('--dpi', type=int, default=DPI,
                          help='DPI для сохранения графика (по умолчанию: %(default)s)')
        
        args = parser.parse_args()
        
        # Настройка вывода для Windows
        if sys.platform == 'win32':
            os.system('color')
        
        # Проверка существования файла
        if not os.path.exists(args.file):
            print(f"Ошибка: Файл '{args.file}' не найден")
            print(f"Текущая директория: {os.getcwd()}")
            print("Доступные файлы в текущей директории:")
            for file in os.listdir():
                print(f"- {file}")
            return
        
        # Загрузка данных
        print(f"\n{'='*50}")
        print(f"Загрузка данных из файла: {args.file}")
        print('='*50)
        df = load_and_prepare_data(args.file)
        
        print(f"\n{'='*50}")
        print("Создание и настройка графиков")
        print('='*50)
        # Создаем фигуру с двумя графиками
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=FIGURE_SIZE)
        
        # Построение графиков
        plot_trading_signals(df, ax1, 'ETH')
        plot_trading_signals(df, ax2, 'BTC')
        
        print(f"\n{'='*50}")
        print("Сохранение результатов")
        print('='*50)
        
        # Настройка общего макета
        print("Настройка макета графиков...")
        plt.tight_layout()
        
        # Сохранение графика
        print(f"Сохранение графика в файл {args.output}...")
        plt.savefig(args.output, dpi=args.dpi, bbox_inches='tight')
        print(f"\nГрафик успешно сохранен как '{args.output}'")
        print('='*50)
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        raise  # Добавляем raise для вывода полного стека ошибки

if __name__ == "__main__":
    main() 