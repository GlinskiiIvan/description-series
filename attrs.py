import pydicom

ds = pydicom.dcmread('/home/brodyga/Загрузки/test/0001. Абдибеков/20231225/S_29535/139373/1393730007.dcm')
# print(dir(ds))

# for element in ds:
#     print(f"{element.tag} - {element.name}: {element.value}")

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
