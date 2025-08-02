import os
import logging
import uuid
from werkzeug.utils import secure_filename

# Try to import PyPDF2 for PDF handling
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyPDF2 not available. PDF text extraction will be limited.")

class FileHandler:
    """Utility class for handling file uploads and text extraction"""
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'txt', 'pdf', 'md', 'csv'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB
    
    def save_file(self, file):
        """
        Save uploaded file and return file path and type
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            tuple: (file_path, file_type)
        """
        try:
            if not self._is_allowed_file(file.filename):
                raise ValueError(f"File type not allowed. Supported types: {', '.join(self.allowed_extensions)}")
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Verify file size
            if os.path.getsize(file_path) > self.max_file_size:
                os.remove(file_path)
                raise ValueError("File size exceeds maximum allowed size (16MB)")
            
            return file_path, file_extension
            
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            raise
    
    def extract_text(self, file_path, file_type):
        """
        Extract text content from uploaded file
        
        Args:
            file_path: Path to the saved file
            file_type: Type of file (extension)
            
        Returns:
            str: Extracted text content
        """
        try:
            if file_type == 'txt' or file_type == 'md':
                return self._extract_text_from_txt(file_path)
            elif file_type == 'pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_type == 'csv':
                return self._extract_text_from_csv(file_path)
            else:
                logging.warning(f"Unsupported file type for text extraction: {file_type}")
                return ""
                
        except Exception as e:
            logging.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_text_from_txt(self, file_path):
        """Extract text from txt/md files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF files"""
        if not PDF_SUPPORT:
            return "PDF text extraction not available. Please install PyPDF2."
        
        try:
            text_content = []
            with open(file_path, 'rb') as file:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            logging.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def _extract_text_from_csv(self, file_path):
        """Extract text from CSV files"""
        try:
            import csv
            text_content = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text_content.append(' | '.join(row))
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logging.error(f"Error extracting text from CSV {file_path}: {e}")
            return ""
    
    def _is_allowed_file(self, filename):
        """Check if file type is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def delete_file(self, file_path):
        """Delete file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path):
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logging.error(f"Error getting file info for {file_path}: {e}")
            return None
