import numpy as np
from PIL import Image, ImageEnhance

image_path = 'тестовые изображения\\фото.jpg'
sharpness = 2.5
contrast = 2.5
brightness = 1.5
threshold = 160

def enhance_image(image_path, sharpness, contrast, brightness):

    image = Image.open(image_path)
    
    # Увеличение резкости
    sharp_enhancer = ImageEnhance.Sharpness(image)
    image = sharp_enhancer.enhance(sharpness)
    
    # Увеличение контраста
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(contrast)
    
    # Увеличение яркости
    brightness_enhancer = ImageEnhance.Brightness(image)
    image = brightness_enhancer.enhance(brightness)
    
    image_rgb = image.convert('RGB')

    return image_rgb

def binarize_image(image_path, threshold):

    image = Image.open(image_path)

    # Переводим в градации серого
    gray_image = image.convert('L')

    # Бинаризация: если пиксель < порога -> 0 (черный), иначе -> 255 (белый)
    bw_image = gray_image.point(lambda x: 0 if x < threshold else 255, '1')

    # Переводим в RGB для корректного чтения (иначе ошибка с типом bool)
    bw_image_rgb = bw_image.convert('RGB')

    return bw_image_rgb

img_bw = binarize_image(image_path, threshold)
img_bw.save('binary_image.jpg')

img_en = enhance_image(image_path, sharpness, contrast, brightness)
img_en.save('enhanced_image.jpg')