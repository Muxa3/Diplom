import win32com.client

for progid in ["V8.COMConnector", "V83.COMConnector", "V85.COMConnector"]:
    try:
        obj = win32com.client.Dispatch(progid)
        print(f"{progid} - УСПЕШНО")
        break
    except Exception as e:
        print(f"{progid} - ошибка: {e}")