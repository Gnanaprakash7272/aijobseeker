import fitz  # PyMuPDF
import docx

def get_text_from_file(file_path: str) -> str:
    """Extracts raw text from a PDF or DOCX file."""
    text = ""
    try:
        if file_path.lower().endswith(".pdf"):
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        elif file_path.lower().endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""
    
    return text.strip()
