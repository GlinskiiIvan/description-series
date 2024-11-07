import pydicom

ds = pydicom.dcmread('/home/brodyga/Загрузки/test/0002. Абдиева Севара/до опер/abdiyeva/DICOM/PA000000/ST000001/SE000001/IM000000')

# Функция для выбора основной директории и возвращения списка её подпапок
def select_file():
    file = input("Введите путь к DICOM-файлу: ").strip().strip("'\"")  # Убираем кавычки вокруг пути, если они есть

    # Проверяем, что директории найдены
    if not file:
        return select_file()
    
    return file

# print(dir(ds))

# for element in ds:
#     print(f"{element.tag} - {element.name}: {element.value}")

# ds = pydicom.dcmread('/home/brodyga/Загрузки/test/0002. Абдиева Севара/до опер/abdiyeva/DICOM/PA000000/ST000001/SE000001/IM000000')
# for element in ds:
#     value = element.value
#     if isinstance(value, bytes):
#         continue  # пропуск байтовых данных
#     print(f"{element.tag} - {element.name}: {value}")

def get_attrs(file):
    ds = pydicom.dcmread(file)
    for element in ds:
        value = element.value
        if isinstance(value, bytes):
            continue  # пропуск байтовых данных
        print(f"{element.tag} - {element.name}: {value}")

# for element in ds:
#     value = element.value
#     if isinstance(value, bytes):
#         try:
#             value = value.decode('utf-8')  # попробуйте 'iso8859-1' или 'utf-16', если utf-8 не подходит
#         except UnicodeDecodeError:
#             value = "Не удалось декодировать"
#     print(f"{element.tag} - {element.name}: {value}")

file = select_file()
get_attrs(file)