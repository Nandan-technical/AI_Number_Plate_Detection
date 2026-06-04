import pytesseract

# Set the correct path to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Check if Tesseract is working
print(pytesseract.get_tesseract_version())
