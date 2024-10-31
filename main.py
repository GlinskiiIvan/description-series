import os
import pydicom
import pandas as pd
from datetime import datetime

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
        # Преобразуем дату из формата 'YYYYMMDD' в 'DD.MM.YYYY'
        return datetime.strptime(dicom_date, "%Y%m%d").strftime("%d.%m.%Y")
    except ValueError:
        return 'N/A'  # Если дата недоступна или невалидна

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

def extract_dicom_info(dicom_file):
    try:
        ds = pydicom.dcmread(dicom_file)
        
        # Извлекаем необходимые данные
        folder_name = os.path.basename(os.path.dirname(dicom_file))  # Название папки
        file_path = dicom_file                                      # Расположение снимка (путь)
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

        return {
            'Folder Name': folder_name,
            'File Path': file_path,
            'Study Date': study_date,
            'Series Number': series_number,
            'Series Description': series_description,
            'Image Orientation': slice_orientation,
            'Modality': modality,
            'Slice Thickness': slice_thickness,
            'Magnetic Field Strength (T)': magnetic_field_strength,
        }
    except Exception as e:
        print(f"Ошибка при обработке {dicom_file}: {e}")
        return None

# Проходим по всем DICOM-файлам и собираем данные
data = []
for root, _, files in os.walk(dicom_dir):
    for file in files:
        if file.lower().endswith('.dcm'):
            dicom_path = os.path.join(root, file)
            info = extract_dicom_info(dicom_path)
            if info:
                data.append(info)

# Сохраняем данные в Excel
df = pd.DataFrame(data)
df.to_excel(output_excel, index=False)
print(f"Данные сохранены в {output_excel}")
