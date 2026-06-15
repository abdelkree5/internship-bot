import re
import logging
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logger = logging.getLogger(__name__)

class CVParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.cv_text = ""
        self.parsed_data = {
            "first_name": "Abdelkreem",
            "last_name": "Abdelhaleem Frahat",
            "email": "abdelkreemfrahat5@gmail.com",
            "phone": "+20 102 545 3847",
            "linkedin": "https://linkedin.com/in/abdelkreem-frahat-160g",
            "github": "https://github.com/abdelkree5",
            "skills": "Python, PyTorch, TensorFlow, Keras, Hugging Face, NLP, LLM, RAG, FastAPI, Flask, Django, AWS, GCP, Docker",
            "education": "Egyptian e-Learning University (EELU) — B.Sc. Computer Science, AI Specialization"
        }

    def extract_text(self):
        """Extract all text from the PDF."""
        if not pdfplumber:
            logger.warning("pdfplumber not installed. Cannot extract text from PDF.")
            return

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                self.cv_text = "\n".join(pages)
                logger.info(f"Successfully extracted {len(self.cv_text)} characters from CV.")
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")

    def parse(self) -> dict:
        """
        Parse the extracted text to find relevant information.
        If extraction fails, returns the default fallback data.
        """
        self.extract_text()
        
        if not self.cv_text:
            logger.info("Using default CV data (update cv_parser/parser.py with your real data if PDF extraction fails).")
            return self.parsed_data

        # Simple Regex based extraction
        # Email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", self.cv_text)
        if email_match:
            self.parsed_data["email"] = email_match.group(0)

        # Phone (simple generic international regex)
        phone_match = re.search(r"\+?\d[\d\s\-\(\)]{8,15}\d", self.cv_text)
        if phone_match:
            self.parsed_data["phone"] = phone_match.group(0).strip()

        # LinkedIn
        linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[\w\-]+", self.cv_text)
        if linkedin_match:
            self.parsed_data["linkedin"] = linkedin_match.group(0)

        # GitHub
        github_match = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[\w\-]+", self.cv_text)
        if github_match:
            self.parsed_data["github"] = github_match.group(0)

        # Name, Skills, Education usually require LLM or strict layout matching.
        # For this skeleton, we recommend manual updating of the self.parsed_data dictionary
        # or integrating an LLM call here to convert `self.cv_text` to JSON.

        logger.info(f"Parsed CV data: {self.parsed_data}")
        return self.parsed_data
