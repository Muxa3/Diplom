import win32com.client

def get_connection():
    try:
        v85 = win32com.client.Dispatch("V85.COMConnector")
        print("Используется V85.COMConnector")
    except Exception:
        v85 = win32com.client.Dispatch("V83.COMConnector")
        print("Используется V83.COMConnector")

    connection_string = 'File="C:\\Users\\Islam\\Documents\\InfoBase";Usr=;Pwd=;'
    try:
        connection = v85.Connect(connection_string)
        print("Подключение к базе успешно установлено.")
        return connection
    except Exception as e:
        print("Ошибка подключения:", e)
        raise

def send_to_1c(data):
    """
    data: словарь с ключами 'Номер направления', 'ФИО', 'СНИЛС', 'Паспорт', 'Услуга'
    """
    print(f"send_to_1c получил: {data}")
    connection = get_connection()
    catalog_patients = connection.Catalogs.Пациенты
    catalog_referrals = connection.Catalogs.Направления

    patient_name = data.get('ФИО')
    # поиск пациента по наименованию (для направления пациент это владелец, т.е. ссылочный тип в 1с
    patient_ref = catalog_patients.НайтиПоНаименованию(patient_name)
    if patient_ref == catalog_patients.ПустаяСсылка():
        new_patient = catalog_patients.CreateItem()
        new_patient.Наименование = patient_name
        new_patient.СНИЛС = data.get('СНИЛС')
        new_patient.Паспорт = data.get('Паспорт')
        new_patient.Write()
        patient_ref = new_patient.Ссылка
        print(f"Создан пациент {patient_name}")
    else:
        print(f"Пациент {patient_name} уже существует")

    # создание направления
    new_referral = catalog_referrals.CreateItem()
    new_referral.НомерНаправления = data.get('Номер направления')
    new_referral.Услуги = data.get('Услуга')
    new_referral.Владелец = patient_ref
    new_referral.Write()
    print(f"Направление {new_referral.Код} записано")