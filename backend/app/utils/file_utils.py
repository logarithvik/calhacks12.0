import os
import shutil
from fastapi import UploadFile
from PyPDF2 import PdfReader
from typing import Optional


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save an uploaded file to disk"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return destination


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    This is a simple implementation - you may want to enhance this
    with better PDF parsing libraries like pdfplumber or PyMuPDF.
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def get_file_extension(filename: str) -> Optional[str]:
    """Get file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None
