import os
import pydicom
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Укажите директорию с DICOM-файлами
dicom_dir = '/home/brodyga/Загрузки/0001. Абдибеков'
output_excel = 'dicom_info.xlsx'

# Функция для определения ориентации
def get_slice_orientation(orientation):
    if orientation == [1, 0, 0, 0, 1, 0]:
        return 'аксиальная'
    elif orientation == [0, 1, 0, 0, 0, -1]:
        return 'сагиттальная'
    elif orientation == [1, 0, 0, 0, 0, -1]:
        return 'корональная'
    return 'неизвестно'

# Функция для преобразования даты
def format_date(dicom_date):
    try:
        return datetime.strptime(dicom_date, "%Y%m%d").strftime("%d.%m.%Y")
    except ValueError:
        return 'N/A'

# Функция для получения типа визуализации
def get_modality_type(modality):
    if 't1*' in modality.lower():
        return 'Т1*'
    if 't1' in modality.lower():
        return 'Т1'
    elif 't2*' in modality.lower():
        return 'Т2*'
    elif 't2' in modality.lower():
        return 'Т2'
    elif 'localizer*' in modality.lower():
        return 'localizer*'
    elif 'localizer' in modality.lower():
        return 'localizer'
    else:
        return modality

# Словарь для хранения информации о сериях и количестве снимков
series_data = defaultdict(list)

# Собираем информацию по всем DICOM-файлам
for root, _, files in os.walk(dicom_dir):
    for file in files:
        if file.lower().endswith('.dcm'):
            dicom_path = os.path.join(root, file)
            try:
                ds = pydicom.dcmread(dicom_path)
                series_uid = getattr(ds, 'SeriesInstanceUID', None)
                if series_uid:
                    # Добавляем файл к соответствующей серии
                    series_data[series_uid].append(dicom_path)
            except Exception as e:
                print(f"Ошибка при обработке {dicom_path}: {e}")

# Собираем данные для каждого уникального идентификатора серии
data = []
for series_uid, file_list in series_data.items():
    first_file = file_list[0]
    try:
        ds = pydicom.dcmread(first_file)

        folder_name = os.path.basename(os.path.normpath(dicom_dir))
        relative_path = os.path.relpath(first_file, start=dicom_dir)
        file_path = os.path.join(os.path.basename(dicom_dir), relative_path)# Расположение снимка (путь)

        study_date = format_date(getattr(ds, 'StudyDate', 'N/A'))                # Дата снимка
        series_number = getattr(ds, 'SeriesNumber', 'N/A')          # Номер серии
        series_description = getattr(ds, 'SeriesDescription', 'N/A') # Название МРТ снимка
        orientation = getattr(ds, 'ImageOrientationPatient', None)
        if orientation:
            slice_orientation = get_slice_orientation([round(val) for val in orientation])
        else:
            slice_orientation = 'N/A'        
        modality = get_modality_type(getattr(ds, 'ProtocolName', 'N/A'))                   # Режим визуализации (Т1, Т2 и др.)
        slice_thickness = getattr(ds, 'SliceThickness', 'N/A')      # Толщина среза
        magnetic_field_strength = getattr(ds, 'MagneticFieldStrength', 'N/A')  # Значение поля, Т

        data.append({
            'Название папки': folder_name,
            'Расположение снимка (путь)': file_path,
            'Дата снимка': study_date,
            'Номер серии': series_number,
            'Количество серии': len(file_list),
            'Название МРТ снимка': series_description,
            'Использование плоскостей': slice_orientation,
            'Режим визуализации (Т1, Т2 и др.)': modality,
            'Толщина среза, Т': slice_thickness,
            'Значение поля (T)': magnetic_field_strength,
        })
    except Exception as e:
        print(f"Ошибка при обработке {first_file}: {e}")

# Сохраняем данные в Excel
df = pd.DataFrame(data)
df.to_excel(output_excel, index=False)
print(f"Данные сохранены в {output_excel}")
