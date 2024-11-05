1) Создание окружения, если не создано:
```shell
python3 -m venv venv
```

2) Установка зависимостей:
```shell
pip install requirements.txt    
```

3) Активация окружения 
Linux:
```shell
source venv/bin/activate
```
Windows:
```shell
.\venv\Scripts\Activate
```

4) Запуск основного скрипта
```shell
python3 main.py
```

5) Выбор корневой директории с DICOM директориями:
```shell
❯ python3 main.py
Введите путь к основной директории с DICOM-папками: 
```
Перетащить в консоль корневую директорию и путь до неё сам пропишется в консоле, либо прописать путь до директории вручную.
