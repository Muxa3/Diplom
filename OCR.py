import json
import os
from PIL import Image, ImageEnhance
import easyocr
import numpy as np

# путь к конфигу
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

# значения по умолчанию (на тот случай если с конфигом что-то не то)
DEFAULT_CONFIG = {
    "keywords": [
        {"field": "Номер направления", "keyword": "НАПРАВЛЕНИЕ", "case_sensitive": True, "x_offset": -140, "y_offset": 140},
        {"field": "ФИО", "keyword": "НАПРАВЛЕНИЕ", "case_sensitive": True, "x_offset": -1560, "y_offset": 280},
        {"field": "СНИЛС", "keyword": "(СНИЛС)", "case_sensitive": True, "x_offset": -1560, "y_offset": 0},
        {"field": "Паспорт", "keyword": "Паспорт", "case_sensitive": True, "x_offset": -40, "y_offset": -20},
        {"field": "Услуга", "keyword": "нужное подчеркнуть", "case_sensitive": True, "x_offset": -140, "y_offset": 10}
    ],
    "sharpness": 2.0,
    "contrast": 1.5,
    "brightness": 1.5,
    "threshold": 160
}

# переменные, которые будут загружены коннфигом
keywords = []
sharpness = 2.0
contrast = 1.5
brightness = 1.5
threshold = 160

# загружает конфигурацию из файла или возвращает словарь по умолчанию
def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        required_keys = {'keywords', 'sharpness', 'contrast', 'brightness', 'threshold'}
        if not required_keys.issubset(config.keys()):
            raise ValueError("В конфиге отсутствуют обязательные ключи")
        return config
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}. Использую значения по умолчанию.")
        return DEFAULT_CONFIG

# перезагружает конфигурацию из файла и обновляет глобальные переменные
def reload_config():
    global keywords, sharpness, contrast, brightness, threshold
    config = load_config()
    keywords = config['keywords']
    sharpness = config['sharpness']
    contrast = config['contrast']
    brightness = config['brightness']
    threshold = config['threshold']
    print("Конфигурация перезагружена")

# инициализируем конфиг
reload_config()

# инициализируем EasyOCR один раз (глобально)
reader = easyocr.Reader(['ru', 'en'])

# меняет четкость, контрастность и яркость изображения
def enhance_image(image_path, sharpness, contrast, brightness):
    image = Image.open(image_path)
    sharp_enhancer = ImageEnhance.Sharpness(image)
    image = sharp_enhancer.enhance(sharpness)
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(contrast)
    brightness_enhancer = ImageEnhance.Brightness(image)
    image = brightness_enhancer.enhance(brightness)
    image_rgb = image.convert('RGB')
    return np.array(image_rgb)

# преобразует все пиксели в изображение либо в черные либо в белые в зависимости от значения theshold
# в большую сторону - больше черного, в меньшую - больше белого
def binarize_image(image_path, threshold):
    image = Image.open(image_path)
    gray_image = image.convert('L')
    bw_image = gray_image.point(lambda x: 0 if x < threshold else 255, '1')
    bw_image_rgb = bw_image.convert('RGB')
    return np.array(bw_image_rgb)

# хватает позицию bbox'а по совпадению из словаря ключевого слова и уже от него ищет блок с текстом по позиции
def extract_by_keywords(image_path, binarization=True):
    
    if binarization:
        img = binarize_image(image_path, threshold)
    else:
        img = enhance_image(image_path, sharpness, contrast, brightness)
    results = reader.readtext(img)

    blocks = []
    for (bbox, text, conf) in results:
        center_x = (bbox[0][0] + bbox[2][0]) / 2
        center_y = (bbox[0][1] + bbox[2][1]) / 2
        blocks.append({
            'text': text,
            'x': center_x,
            'y': center_y,
            'bbox': bbox
        })

    extracted = {}
    for keyword in keywords:
        # Ищем блок, содержащий ключевое слово
        if keyword['case_sensitive']:
            word = keyword['keyword']
            for block in blocks:
                if word in block['text']:
                    target_y = block['y']
                    target_x = block['x']
                    candidates = []
                    for other in blocks:
                        if other['y'] > target_y + keyword['y_offset'] and other['x'] > target_x + keyword['x_offset']:
                            candidates.append((other['x'], other['y'], other['text']))
                        if candidates:
                            # берём первого попавшегося
                            extracted[keyword['field']] = candidates[0][2]
                            break
        else:
            word = keyword['keyword'].lower()
            for block in blocks:
                if word in block['text'].lower():
                    target_y = block['y']
                    target_x = block['x']
                    candidates = []
                    for other in blocks:
                        if other['y'] > target_y + keyword['y_offset'] and other['x'] > target_x + keyword['x_offset']:
                            candidates.append((other['x'], other['y'], other['text']))
                        if candidates:
                            # то же самое
                            candidates.sort()
                            extracted[keyword['field']] = candidates[0][2]
                            break

    return extracted