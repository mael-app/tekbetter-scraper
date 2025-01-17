import os

from dotenv import load_dotenv

from app.logger import log_info, log_error, log_warning


def check_env_variables():
    log_info("Loading environment variables")
    load_dotenv()
    valid = True
    if not os.getenv("TEKBETTER_API_URL"):
        log_error("Missing TEKBETTER_API_URL environment variable")
        valid = False
    if not os.getenv("SCRAPER_MODE"):
        log_warning("Missing SCRAPER_MODE environment variable. Using default value 'private'")
    if os.getenv("SCRAPER_MODE") == "public" and not os.getenv("PUBLIC_SCRAPER_TOKEN"):
        log_error("Missing PUBLIC_SCRAPER_TOKEN environment variable")
        valid = False
    if not os.getenv("SCRAPER_CONFIG_FILE") and os.getenv("SCRAPER_MODE") == "private":
        log_error("Missing SCRAPER_CONFIG_FILE environment variable")
        valid = False
    else:
        if not os.path.exists(os.getenv("SCRAPER_CONFIG_FILE")):
            log_error("Invalid SCRAPER_CONFIG_FILE path")
            valid = False
        if not os.access(os.getenv("SCRAPER_CONFIG_FILE"), os.R_OK):
            log_error(f"{os.getenv('SCRAPER_CONFIG_FILE')} is not readable")
            valid = False
        if not os.access(os.getenv("SCRAPER_CONFIG_FILE"), os.W_OK):
            log_error(f"{os.getenv('SCRAPER_CONFIG_FILE')} is not writable")
            valid = False
    return valid