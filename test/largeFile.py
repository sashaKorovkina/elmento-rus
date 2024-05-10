file = r"C:\Users\sasha\Desktop\Elmento-Materials\war-and-peace.pdf"

import io
import fitz
import pytesseract
from PIL import Image
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\sasha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def get_pdf_images_and_texts(pdf_path):
    start_time = time.time()
    doc = fitz.open(pdf_path)
    pdf_images = []
    pdf_texts = []  # List to store text from all pages

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_data = pix.tobytes()
        pdf_image = Image.open(io.BytesIO(image_data))
        pdf_images.append(pdf_image)

        text = pytesseract.image_to_string(pdf_image, lang='rus')
        pdf_texts.append(text)
        #print(text)

    end_time = time.time()  # End the timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print("Elapsed Time:", elapsed_time, "seconds")

    return pdf_images, pdf_texts

pdf_images, pdf_texts = get_pdf_images_and_texts(file)
