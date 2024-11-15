import os
import pydicom
import pandas as pd
from datetime import datetime
from collections import defaultdict
from PIL import Image
import numpy as np
from datetime import datetime
import re

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

# Функция для конвертации DICOM в PNG с нормализацией яркости
def convert_dicom_to_png(dicom_dir, dicom_path, output_dir, modality, slice_orientation):
    patient_number = os.path.basename(dicom_dir)
    # Чтение DICOM файла
    ds = pydicom.dcmread(dicom_path)
    image_data = ds.pixel_array
    series_number = str(getattr(ds, 'SeriesNumber', 'N/A'))          # Номер серии

    # Нормализация яркости для корректного отображения
    image_data = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data)) * 255
    image_data = image_data.astype(np.uint8)  # Конвертируем в 8-битный формат
    
    # Создание изображения и сохранение в формате PNG
    img = Image.fromarray(image_data)

    # Создание конечного пути для сохранения изображения
    output_subdir = os.path.join(output_dir, patient_number, modality, slice_orientation)
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
        
# Функция для проверки части тела на колено
def is_knee(body_part, study_description):
    return ('knee' in body_part) or ('ankle' in body_part) or ('knee' in study_description) or ('ks' in study_description) or ('kolen' in study_description) or ('kalen' in study_description) or ('kolan' in study_description) or ('kalan' in study_description)

# Функция для проверки режима визуализации
# T1/T2/PD/STIR/FLAIR
def is_allowed_mode(series_description):
    return ('t1' in series_description) or ('t2' in series_description) or ('pd' in series_description) or ('stir' in series_description) or ('flair' in series_description)

# Основная функция обработки DICOM файлов
def process_dicom_files(directories, output_excel='dicom_info.xlsx', output_dir='sorted_images'):
    # Создаем директории для PNG изображений
    # os.makedirs(os.path.join(output_dir, 'аксиальная'), exist_ok=True)
    # os.makedirs(os.path.join(output_dir, 'сагиттальная'), exist_ok=True)
    # os.makedirs(os.path.join(output_dir, 'корональная'), exist_ok=True)
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
                # modality = get_modality_type(getattr(ds, 'ProtocolName', 'N/A'))                   # Режим визуализации (Т1, Т2 и др.)
                modality = parse_modality(series_description)                   # Режим визуализации (Т1, Т2 и др.)
                slice_thickness = getattr(ds, 'SliceThickness', 'N/A')      # Толщина среза
                magnetic_field_strength = getattr(ds, 'MagneticFieldStrength', 'N/A')  # Значение поля, Т

                # Проверка, что изображение относится к колену
                body_part = getattr(ds, 'BodyPartExamined', '').lower()
                study_description = getattr(ds, 'StudyDescription', '').lower()
                Performed_Procedure_Step_escription = getattr(ds, 'PerformedProcedureStepDescription', '').lower()

                print('Обрабатывается: ', file_path)

                # if ('knee' in body_part) or ('ankle' in body_part) or ('knee' in study_description) or ('ks' in study_description) or ('kolen' in study_description) or ('kalen' in study_description) or ('kolan' in study_description) or ('kalan' in study_description):
                if is_knee(body_part, study_description):
                    # if not ('localizer' in series_description.lower()) and not ('default' in series_description.lower()) and not ('survey' in series_description.lower()) and not ('screen' in series_description.lower()) and not ('plane' in series_description.lower()) and not ('calibration' in series_description.lower()):
                    if is_allowed_mode(series_description):
                        data.append({
                            'Название папки': folder_name,
                            'Расположение снимка (путь)': file_path,
                            'Дата снимка': study_date,
                            # 'Номер серии': series_number,
                            'Количество серии': len(file_list),
                            'Название МРТ снимка': series_description,
                            'Использование плоскостей': slice_orientation,
                            'Режим визуализации (Т1, Т2 и др.)': modality,
                            'Толщина среза, Т': slice_thickness,
                            'Значение поля (T)': magnetic_field_strength,
                            'body_part': body_part,
                            'study_description': study_description,
                        })
                        # Конвертация в PNG и сохранение в соответствующей директории
                        output_subdir = os.path.join(output_dir, slice_orientation)
                        for dicom_file in file_list:
                            convert_dicom_to_png(dicom_dir, dicom_file, output_dir, modality, slice_orientation)
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