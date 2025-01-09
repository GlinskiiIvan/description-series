import pydicom

# ds = pydicom.dcmread('/home/brodyga/Загрузки/test/0002. Абдиева Севара/до опер/abdiyeva/DICOM/PA000000/ST000001/SE000001/IM000000')

# Функция для выбора основной директории и возвращения списка её подпапок
def select_file():
    file = input("Введите путь к DICOM-файлу: ").strip().strip("'\"")  # Убираем кавычки вокруг пути, если они есть

    # Проверяем, что директории найдены
    if not file:
        return select_file()
    
    return file

def get_attrs(file):
    ds = pydicom.dcmread(file)
    for element in ds:
        value = element.value
        if isinstance(value, bytes):
            continue  # пропуск байтовых данных
        print(f"{element.tag} - {element.name}: {value}")

def extract_methods_from_dicom(file_path):
    ds = pydicom.dcmread(file_path)

    methods = []
    # Читаем ключевые атрибуты
    if "SequenceVariant" in ds:
        methods.append(ds.SequenceVariant)
    if "ScanOptions" in ds:
        methods.append(ds.ScanOptions)
    if "SequenceName" in ds:
        methods.append(ds.SequenceName)
    if "PulseSequenceName" in ds:
        methods.append(ds.PulseSequenceName)
    if "ImageType" in ds:
        methods.extend(ds.ImageType)

    # Объединяем и фильтруем уникальные методы
    methods = [str(method).strip() for method in methods if method]
    return list(set(methods))

file = select_file()
# get_attrs(file)
print(extract_methods_from_dicom(file))