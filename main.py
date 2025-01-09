import os
import pydicom
import pandas as pd
from datetime import datetime
from collections import defaultdict
from PIL import Image
import numpy as np
from datetime import datetime
import re
from typing import List
import cv2

# Укажите директорию с DICOM-файлами
output_excel = 'dicom_info.xlsx'

# Функция для выбора основной директории и возвращения списка её подпапок
def select_directories():
    main_directory = input("Введите путь к основной директории с DICOM-папками: ").strip().strip("'\"")
    
    # Проверяем, что путь существует и является директорией
    if not os.path.isdir(main_directory):
        print("Указанный путь не является директорией. Повторите попытку.")
        return select_directories()
    
    # Собираем все директории внутри основной директории
    # directories = [os.path.join(main_directory, d) for d in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, d))]
    
    # Собираем и сортируем директории внутри основной директории
    directories = sorted(
        [os.path.join(main_directory, d) for d in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, d))],
        key=lambda x: os.path.basename(x)
    )

    # Проверяем, что директории найдены
    if not directories:
        print("В указанной директории нет вложенных директорий. Повторите попытку.")
        return select_directories()
    
    return directories


# Функция для определения ориентации 
def get_slice_orientation(orientation):
    # Округление значений
    # orientation = [round(val, 3) for val in orientation]

    if orientation == [1, 0, 0, 0, 1, 0]:
        return 'аксиальная'
    elif orientation == [0, 1, 0, 0, 0, -1]:
        return 'сагиттальная'
    elif orientation == [1, 0, 0, 0, 0, -1]:
        return 'корональная'
    return 'косой срез'

# Функция для определения ориентации из названия файла
def get_slice_orientation_from_series_description(series_description):
    if 'tra' in series_description:
        return 'аксиальная'
    elif 'sag' in series_description:
        return 'сагиттальная'
    elif 'cor' in series_description:
        return 'корональная'
    return 'N/A'

# Функция для преобразования даты
def format_date(dicom_date):
    try:
        return datetime.strptime(dicom_date, "%Y%m%d").strftime("%d.%m.%Y")
    except ValueError:
        return 'N/A'

# Функция для конвертации DICOM в PNG с нормализацией яркости
def convert_dicom_to_png(dicom_dir, dicom_path, output_dir, modality, slice_orientation, methods, apply_clahe=True, apply_laplacian=True):
    # Чтение DICOM файла
    ds = pydicom.dcmread(dicom_path)
    image_data = ds.pixel_array

    patient_number = os.path.basename(dicom_dir)
    series_number = str(getattr(ds, 'SeriesNumber', 'N/A'))

    # Нормализация яркости для корректного отображения
    image_data = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data)) * 255
    image_data = image_data.astype(np.uint8)  # Конвертируем в 8-битный формат
    
    # Применение CLAHE (по желанию)
    if apply_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image_data = clahe.apply(image_data)

    # Применение фильтра Лапласа для усиления краев (по желанию)
    if apply_laplacian:
        laplacian = cv2.Laplacian(image_data, cv2.CV_64F)
        laplacian_abs = cv2.convertScaleAbs(laplacian)
        image_data = cv2.addWeighted(image_data, 1.0, laplacian_abs, 0.5, 0)

    # Создание изображения и сохранение в формате PNG
    img = Image.fromarray(image_data)

    # Создание конечного пути для сохранения изображения
    # output_subdir = os.path.join(output_dir, patient_number, modality, slice_orientation, '-'.join(methods))
    output_subdir = os.path.join(output_dir, modality, slice_orientation, '-'.join(methods))
    # output_subdir = os.path.join(output_dir, modality, '-'.join(methods))
    os.makedirs(output_subdir, exist_ok=True)
    
    # Генерация имени файла без расширения .dcm
    # filename = patient_number + "-" + series_number + "-" +  os.path.splitext(os.path.basename(dicom_path))[0] + ".png"
    filename = f"{patient_number}-{series_number}-{os.path.splitext(os.path.basename(dicom_path))[0]}.png"
    output_path = os.path.join(output_subdir, filename)
    
    img.save(output_path)
    print(f"Сохранено: {output_path}")

# Функция для получения стандартизированного типа визуализации
def parse_modality(modality_str):
    modality_str = modality_str.lower()

    if 't1' in modality_str:
        return 'T1'
    elif 't2' in modality_str:
        return 'T2*' if 't2*' in modality_str else 'T2'
    elif 'pd' in modality_str:
        return 'PD'
    elif 'stir' in modality_str:
        return 'STIR'
    elif 'flair' in modality_str:
        return 'FLAIR'

    else:
        return modality_str
        

# Функция для получения стандартизированного типа доаолнительных методов
def parse_dop_modality(modality_str):
    modality_str = modality_str.lower()

    if 'fs' in modality_str:
        return 'FSE' if 'fse' in modality_str else 'FS'
    elif 'tse' in modality_str:
        return 'TSE'
    elif 'rse' in modality_str:
        return 'RSE'
    elif 'spair' in modality_str:
        return 'SPAIR'
    else:
        return modality_str

# Функция для проверки части тела на колено
def is_knee(body_part, study_description):
    return ('knee' in body_part) or ('ankle' in body_part) or ('knee' in study_description) or ('ks' in study_description) or ('kolen' in study_description) or ('kalen' in study_description) or ('kolan' in study_description) or ('kalan' in study_description)

# Функция для проверки режима визуализации
# T1/T2/PD/STIR/FLAIR
def is_allowed_mode(series_description):
    return ('t1' in series_description) or ('t2' in series_description) or ('pd' in series_description)
    # return ('t1' in series_description) or ('t2' in series_description) or ('pd' in series_description) or ('stir' in series_description) or ('flair' in series_description)

# Функция для проверки дополнительного режима
# FS/FSE/TSE...
def is_allowed_dop_mode(series_description):
    return ('FSE' in series_description) or ('TSE' in series_description) or ('FS' in series_description) or ('FSAT' in series_description) or ('FATSAT' in series_description) or ('SE' in series_description)
    # return ('fse' in series_description) or ('tse' in series_description) or ('rse' in series_description) or ('fs' in series_description) or ('se' in series_description) or ('spair' in series_description)

def extract_methods_from_name(image_name: str) -> List[str]:
    # Словарь методов визуализации с уточнением шаблонов
    methods = {
        "FSE": r"(?:_|^| )fse(?:_| |$)", 
        # "FFE": r"(?:_|^| )ffe(?:_| |$)", 
        # "IRFFE": r"(?:_|^| )irffe(?:_| |$)", 
        "TSE": r"(?:_|^| )tse(?:_| |$)",  
        # "IR-TSE": r"(?:_|^| )ir-tse(?:_| |$)",  
        # "ATSE": r"(?:_|^| )atse(?:_| |$)",  
        # "STIR": r"(?:_|^| )stir(?:_| |$)",  
        # "SPIR": r"(?:_|^| )spir(?:_| |$)",  
        # "SPAIR": r"(?:_|^| )spair(?:_| |$)",  
        "FS": r"(?:_|^| )fs(?:_| |$)",  
        "FSAT": r"(?:_|^| )fsat(?:_| |$)",  
        # "FSIR": r"(?:_|^| )fsir(?:_| |$)",  
        "FATSAT": r"(?:_|^| )fatsat(?:_| |$)",  
        "FATSAT": r"(?:_|^| )fat sat(?:_| |$)",  
        # "FAT": r"(?:_|^| )fat(?:_| |$)",  
        # "FGRE": r"(?:_|^| )fgre(?:_| |$)",  
        # "GRE": r"(?:_|^| )gre(?:_| |$)",  
        # "GRE2D": r"(?:_|^| )gre2d(?:_| |$)",  
        # "IR": r"(?:_|^| )ir(?:_| |$)",  
        # "FRFSE": r"(?:_|^| )frfse(?:_| |$)",  
        # "PROP": r"(?:_|^| )prop(?:_| |$)",  
        # "TIRM": r"(?:_|^| )tirm(?:_| |$)",  
        # "DIXON": r"(?:_|^| )dixon(?:_| |$)",  
        # "TRUFI": r"(?:_|^| )trufi(?:_| |$)",  
        "SE": r"(?:_|^| )se(?:_| |$)"  
    }

    # Приведение строки к нижнему регистру
    image_name = image_name.lower()

    # Поиск совпадений
    detected_methods = [method for method, pattern in methods.items() if re.search(pattern, image_name)]
    
    return detected_methods

# Основная функция обработки DICOM файлов
def process_dicom_files(directories, output_excel='dicom_info.xlsx', output_dir='sorted_images'):
    # Создаем директории для PNG изображений
    os.makedirs(output_dir, exist_ok=True)

    data = []

    # Собираем данные по всем DICOM-файлам в выбранных директориях
    for dicom_dir in directories:
        series_data = defaultdict(list)
        for root, _, files in os.walk(dicom_dir):
            for file in files:
                dicom_path = os.path.join(root, file)
                
                # Проверяем, если файл является DICOM, пытаясь его прочитать
                try:
                    ds = pydicom.dcmread(dicom_path)
                    series_uid = getattr(ds, 'SeriesInstanceUID', None)
                    if series_uid:
                        # Добавляем файл к соответствующей серии
                        series_data[series_uid].append(dicom_path)
                except pydicom.errors.InvalidDicomError:
                    # Пропускаем, если файл не является DICOM
                    continue
                except Exception as e:
                    print(f"Ошибка при обработке {dicom_path}: {e}")

        # Обрабатываем каждый уникальный идентификатор серии
        for series_uid, file_list in series_data.items():
            # Сортируем список файлов в серии по имени файла
            file_list = sorted(file_list, key=lambda x: os.path.basename(x))
            first_file = file_list[0]
            try:
                ds = pydicom.dcmread(first_file)

                folder_name = os.path.basename(os.path.normpath(dicom_dir))
                relative_path = os.path.relpath(first_file, start=dicom_dir)
                file_path = os.path.join(os.path.basename(dicom_dir), relative_path)# Расположение снимка (путь)

                study_date = format_date(getattr(ds, 'StudyDate', 'N/A'))                # Дата снимка
                series_number = getattr(ds, 'SeriesNumber', 'N/A')          # Номер серии
                series_description = getattr(ds, 'SeriesDescription', 'N/A').lower() # Название МРТ снимка
                orientation = getattr(ds, 'ImageOrientationPatient', None)
                if orientation:
                    slice_orientation = get_slice_orientation([round(val) for val in orientation])
                else:
                    slice_orientation = 'N/A'        
                modality = parse_modality(series_description)                   # Режим визуализации (Т1, Т2 и др.)
                slice_thickness = getattr(ds, 'SliceThickness', 'N/A')      # Толщина среза
                magnetic_field_strength = getattr(ds, 'MagneticFieldStrength', 'N/A')  # Значение поля, Т

                # Проверка, что изображение относится к колену
                body_part = getattr(ds, 'BodyPartExamined', '').lower()
                study_description = getattr(ds, 'StudyDescription', '').lower()
                Performed_Procedure_Step_escription = getattr(ds, 'PerformedProcedureStepDescription', '').lower()

                methods = extract_methods_from_name(series_description)

                print('Обрабатывается: ', file_path)

                if is_knee(body_part, study_description):
                    if is_allowed_mode(series_description):
                        if is_allowed_dop_mode(methods):
                            if slice_orientation != 'N/A':
                                data.append({
                                    'Название папки': folder_name,
                                    'Расположение снимка (путь)': file_path,
                                    'Дата снимка': study_date,
                                    # 'Номер серии': series_number,
                                    'Количество серии': len(file_list),
                                    'Название МРТ снимка': series_description,
                                    'Использование плоскостей': slice_orientation,
                                    'Использование плоскостей из названия снимка (N/a)': '',
                                    'Значение плоскости': orientation,
                                    'Режим визуализации (Т1, Т2 и др.)': modality,
                                    'Доп методы': methods,
                                    'Толщина среза, Т': slice_thickness,
                                    'Значение поля (T)': magnetic_field_strength,
                                    'body_part': body_part,
                                    'study_description': study_description,
                                })
                            if slice_orientation == 'N/A':
                                slice_orientation = get_slice_orientation_from_series_description(series_description)
                                data.append({
                                    'Название папки': folder_name,
                                    'Расположение снимка (путь)': file_path,
                                    'Дата снимка': study_date,
                                    # 'Номер серии': series_number,
                                    'Количество серии': len(file_list),
                                    'Название МРТ снимка': series_description,
                                    'Использование плоскостей': '',
                                    'Использование плоскостей из названия снимка (N/a)': slice_orientation,
                                    'Значение плоскости': orientation,
                                    'Режим визуализации (Т1, Т2 и др.)': modality,
                                    'Доп методы': methods,
                                    'Толщина среза, Т': slice_thickness,
                                    'Значение поля (T)': magnetic_field_strength,
                                    'body_part': body_part,
                                    'study_description': study_description,
                                })

                            # Конвертация в PNG и сохранение в соответствующей директории
                            # for dicom_file in file_list:
                            #     convert_dicom_to_png(dicom_dir, dicom_file, output_dir, modality, slice_orientation, methods, False, False)
            except Exception as e:
                print(f"Ошибка при обработке {first_file}: {e}")

    # Преобразуем данные в DataFrame и сохраняем
    new_df = pd.DataFrame(data)
    if os.path.exists(output_excel):
        existing_df = pd.read_excel(output_excel)
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df
    final_df.to_excel(output_excel, index=False)
    print(f"Данные сохранены в {output_excel}")

# Запуск интерактивного выбора и обработки
start_time = datetime.now()
directories = select_directories()
process_dicom_files(directories)
end_time = datetime.now()

execution_time = end_time - start_time
print(f"Время выполнения скрипта: {execution_time}")