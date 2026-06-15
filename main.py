import sys
import logging
from config import CV_PDF_PATH, LOGS_DIR
import database.db as db
from cv_parser.parser import CVParser
from automation.browser import ApplicationBrowser
from automation.filler import FormFiller
from notifications.telegram import notify_ready_to_submit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("main")

def apply_for_job(url: str, company: str, role: str):
    logger.info(f"Starting application process for {role} at {company}")
    
    # Check duplicates
    if db.has_applied(url, company, role):
        logger.warning(f"Already applied for {role} at {company}. Skipping.")
        return

    # Parse CV
    logger.info("Parsing CV...")
    parser = CVParser(CV_PDF_PATH)
    cv_data = parser.parse()

    # Start Browser
    browser_mgr = ApplicationBrowser()
    browser_mgr.start(headless=False)  # Keep headful so user can interact and submit
    
    try:
        # Navigate
        browser_mgr.navigate(url)
        
        # Fill Form
        filler = FormFiller(browser_mgr, cv_data, CV_PDF_PATH)
        filler.fill_generic_form()
        filler.upload_cv()
        
        # Notify
        notify_ready_to_submit(company, role, url)
        
        # Wait for user confirmation before proceeding
        filler.wait_for_user_confirmation()
        
        # Ask if successfully submitted to record in DB
        status = input(f"Did you successfully submit the application for {company}? (y/n): ")
        if status.lower().strip() == 'y':
            db.record_application(company, role, url, status="Submitted")
            logger.info(f"Successfully recorded application for {company}.")
        else:
            db.record_application(company, role, url, status="Skipped/Failed")
            logger.info(f"Recorded application as skipped/failed.")
            
    except Exception as e:
        logger.error(f"An error occurred during automation: {e}")
    finally:
        browser_mgr.stop()

def main():
    db.init_db()
    
    print("Welcome to the Internship Automation System!")
    print("------------------------------------------")
    url = input("Enter the Job Application URL: ")
    company = input("Enter the Company Name: ")
    role = input("Enter the Role: ")
    
    if url and company and role:
        apply_for_job(url, company, role)
    else:
        print("Invalid inputs. URL, Company, and Role are required.")

if __name__ == "__main__":
    main()
