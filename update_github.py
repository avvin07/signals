import subprocess
import sys
import os
import webbrowser

def run_git_command(command):
    """
    Выполняет указанную Git-команду через subprocess.run.
    Печатает stdout и stderr команды.
    Возвращает True при успешном выполнении (exit code 0), иначе False.
    """
    # Запуск команды в shell и захват вывода
    try:
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            shell=True, 
            text=True
        )
        # Печать стандартного вывода команды Git
        print(result.stdout)
        # Обработка ошибок и предупреждений
        if result.stderr and result.returncode != 0:
            print(f"Ошибка: {result.stderr}")  # ошибка при выполнении Git-команды
        elif result.stderr:
            print(f"Предупреждение: {result.stderr}")  # предупреждение от Git
        return result.returncode == 0
    except Exception as e:
        # Обработка непредвиденных исключений при выполнении команды
        print(f"Ошибка при выполнении команды: {e}")
        return False

def main():
    """
    Основная функция скрипта:
    Последовательно выполняет все шаги по обновлению репозитория.
    """
    print("===== Обновление репозитория на GitHub =====")
    
    # 1) Настройка remote 'origin'
    # Получаем текущую конфигурацию remotes через 'git remote -v'
    remote_info = subprocess.run(
        "git remote -v",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    )
    
    if remote_info.returncode != 0 or "origin" not in remote_info.stdout:
        # Если 'origin' не найден или произошла ошибка при запросе
        # Запрашиваем у пользователя URL репозитория и добавляем его
        print("Не найден удаленный репозиторий 'origin'.")
        repo_url = input("Введите URL вашего GitHub репозитория: ")
        if not repo_url:
            print("URL репозитория не указан. Операция отменена.")
            return
        
        if not run_git_command(f"git remote add origin {repo_url}"):
            print("Не удалось добавить удаленный репозиторий.")
            return
    else:
        # Если 'origin' существует, показываем текущий URL и предлагаем изменить
        print("Текущий удаленный репозиторий:")
        print(remote_info.stdout)
        
        change_remote = input("Хотите изменить URL репозитория? (y/n): ")
        if change_remote.lower() in ['y', 'yes', 'да']:
            repo_url = input("Введите новый URL вашего GitHub репозитория: ")
            if not repo_url:
                print("URL репозитория не указан. Операция отменена.")
                return
                
            if not run_git_command(f"git remote set-url origin {repo_url}"):
                print("Не удалось обновить URL удаленного репозитория.")
                return
    
    # 2) Определение текущей ветки для пуша
    # Выполняем 'git branch --show-current' и получаем имя ветки
    current_branch = subprocess.run(
        "git branch --show-current",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    ).stdout.strip()
    
    if not current_branch:
        # Если не удалось определить ветку через Git, запрашиваем у пользователя (main/master)
        print("Не удалось определить текущую ветку.")
        branch_name = input("Введите имя ветки для отправки на GitHub (обычно main или master): ")
        if not branch_name:
            branch_name = "main"
    else:
        branch_name = current_branch
        print(f"Текущая ветка: {branch_name}")
    
    # 3) Проверка статуса репозитория и коммит изменений
    # 'git status --porcelain' отображает незакоммиченные изменения
    status = subprocess.run(
        "git status --porcelain",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    ).stdout.strip()
    
    if status:
        # Есть изменения: выводим их и при подтверждении автоматически коммитим
        print("\nНеотправленные изменения:")
        print(status)
        
        commit_changes = input("Хотите закоммитить все изменения перед отправкой на GitHub? (y/n): ")
        if commit_changes.lower() in ['y', 'yes', 'да']:
            commit_message = input("Введите сообщение коммита: ")
            if not commit_message:
                commit_message = "Обновление файлов"
            
            if not run_git_command("git add ."):
                print("Не удалось добавить файлы в индекс.")
                return
                
            if not run_git_command(f'git commit -m "{commit_message}"'):
                print("Не удалось создать коммит.")
                return
    
    # 4) Публикация изменений на GitHub (git push)
    # Устанавливаем upstream и отправляем ветку на удалённый сервер
    print(f"\nОтправка изменений в ветку {branch_name} на GitHub...")
    if not run_git_command(f"git push -u origin {branch_name}"):
        # Push не удался: возможные причины и предложение выполнить pull
        print("\nНе удалось отправить изменения. Возможные причины:")
        print("1. Проблемы с аутентификацией (учетные данные)")
        print("2. Конфликты с удаленным репозиторием")
        print("3. Отсутствие прав на запись в репозиторий")
        
        pull_first = input("\nПопробовать сначала получить изменения с GitHub (git pull)? (y/n): ")
        if pull_first.lower() in ['y', 'yes', 'да']:
            if run_git_command(f"git pull origin {branch_name}"):
                print("\nИзменения успешно получены. Повторная попытка отправки...")
                if run_git_command(f"git push -u origin {branch_name}"):
                    print("\nУспешно! Ваш код обновлен на GitHub.")
                else:
                    print("\nНе удалось отправить изменения даже после получения обновлений.")
            else:
                print("\nНе удалось получить изменения с GitHub.")
    else:
        # Push прошёл успешно: получаем URL репозитория и открываем в браузере
        print("\nУспешно! Ваш код обновлен на GitHub.")
        
        # Получаем URL репозитория
        remote_url = subprocess.run(
            "git remote get-url origin",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        ).stdout.strip()
        
        if remote_url:
            # Преобразуем URL, если он заканчивается на .git
            if remote_url.endswith('.git'):
                remote_url = remote_url[:-4]
                
            # Преобразуем SSH URL в HTTP URL для открытия в браузере
            if remote_url.startswith("git@github.com:"):
                remote_url = "https://github.com/" + remote_url[15:]
                
            print(f"URL вашего репозитория: {remote_url}")
            open_repo = input("Открыть репозиторий в браузере? (y/n): ")
            if open_repo.lower() in ['y', 'yes', 'да']:
                webbrowser.open(remote_url)

if __name__ == "__main__":
    main() 