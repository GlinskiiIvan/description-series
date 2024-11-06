1) Создание окружения, если не создано

   Linux:
```shell
python3 -m venv venv
```
  Windows:
```shell
python -m venv venv
```

2) Активация окружения 

   Linux:
```shell
source venv/bin/activate
```
  Windows:
```shell
.\venv\Scripts\Activate
```

3) Установка зависимостей

   linux:
```shell
pip install requirements.txt    
```
  Windows:
```shell
python -m pip install requirements.txt
```

4) Запуск основного скрипта

   Linux:
```shell
python3 main.py
```
  Windows:
```shell
python main.py
```

5) Выбор корневой директории с DICOM директориями:
```shell
Введите путь к основной директории с DICOM-папками: 
```
Перетащить в консоль корневую директорию и путь до неё сам пропишется в консоле, либо прописать путь до директории вручную.
