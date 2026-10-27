import os
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import cbio_logger

CBIO_USERNAME_VAR = "CBIO_USERNAME"
CBIO_PASSWORD_VAR = "CBIO_PASSWORD"

def get_cbio_session_id() -> str:
    """
    Logs into the cBioPortal website using credentials from environment variables
    and retrieves the JSESSIONID cookie.

    Ensure the env vars CBIO_USERNAME and CBIO_PASSWORD are set before running this function.

    Returns:
        str: The JSESSIONID cookie value.

    Raises:
        ValueError: If the CBio credentials are missing or the JSESSIONID cookie cannot be retrieved.
    """

    logger = cbio_logger.initialize_logging(__name__)

    # Get env vars for CBIO_USERNAME and CBIO_PASSWORD
    CBIO_USERNAME = os.getenv(CBIO_USERNAME_VAR)
    CBIO_PASSWORD = os.getenv(CBIO_PASSWORD_VAR)

    if not CBIO_USERNAME or not CBIO_PASSWORD:
        err_message = "CBio credentials missing, did not attempt to login. Please set the environment variables CBIO_USERNAME and CBIO_PASSWORD"
        logger.error(err_message)
        raise ValueError(err_message)
        
    jsesssion_id = None

    logger.info("Logging into cBioPortal via Playwright...")
    # Start Playwright and launch a headless browser
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to the cBioPortal login page
    page.goto("https://cbioportal.ca/")
    page.wait_for_url("https://cbioportal.pmgenomics.ca/auth/realms/cbio-uhn/login-actions/authenticate?client_id=cbioportal")

    # Fill in the username and password fields
    username = page.locator("#username")
    username.fill(CBIO_USERNAME)

    password = page.locator("#password")
    password.fill(CBIO_PASSWORD)

    # Click the login button
    login_btn = page.locator("#kc-login")
    login_btn.click()

    # Retrieve the storage state (including cookies)
    state = context.storage_state()
    cookies = state["cookies"]

    # Extract the JSESSIONID cookie value
    for item in cookies:
        if item["name"] == "JSESSIONID":
            jsesssion_id = item["value"]

    # Raise an error if the JSESSIONID cookie was not found
    if not jsesssion_id:
        err_message = "Could not retrieve the JSESSIONID cookie"
        logger.error(err_message)
        raise ValueError(err_message)
    
    logger.info("Successfully logged into cBioPortal and retrieved the JSESSIONID cookie")
    return jsesssion_id

async def async_get_cbio_session_id() -> str:
    """
    Asyncronously logs into the cBioPortal website using credentials from environment variables
    and retrieves the JSESSIONID cookie.

    Ensure the env vars CBIO_USERNAME and CBIO_PASSWORD are set before running this function.

    Returns:
        str: The JSESSIONID cookie value.

    Raises:
        ValueError: If the CBio credentials are missing or the JSESSIONID cookie cannot be retrieved.
    """

    logger = cbio_logger.initialize_logging(__name__)

    # Get env vars for CBIO_USERNAME and CBIO_PASSWORD
    CBIO_USERNAME = os.getenv(CBIO_USERNAME_VAR)
    CBIO_PASSWORD = os.getenv(CBIO_PASSWORD_VAR)

    if not CBIO_USERNAME or not CBIO_PASSWORD:
        err_message = "CBio credentials missing, did not attempt to login. Please set the environment variables CBIO_USERNAME and CBIO_PASSWORD"
        logger.error(err_message)
        raise ValueError(err_message)
        
    jsesssion_id = None

    logger.info("Logging into cBioPortal via Playwright...")
    # Start Playwright and launch a headless browser
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to the cBioPortal login page
        await page.goto("https://cbioportal.ca/")
        await page.wait_for_url("https://cbioportal.pmgenomics.ca/auth/realms/cbio-uhn/login-actions/authenticate?client_id=cbioportal")

        # Fill in the username and password fields
        username = page.locator("#username")
        await username.fill(CBIO_USERNAME)

        password = page.locator("#password")
        await password.fill(CBIO_PASSWORD)

        # Click the login button
        login_btn = page.locator("#kc-login")
        await login_btn.click()

        # Retrieve the storage state (including cookies)
        state = await context.storage_state()
        cookies = state["cookies"]

        # Extract the JSESSIONID cookie value
        for item in cookies:
            if item["name"] == "JSESSIONID":
                jsesssion_id = item["value"]

        # Raise an error if the JSESSIONID cookie was not found
        if not jsesssion_id:
            err_message = "Could not retrieve the JSESSIONID cookie"
            logger.error(err_message)
            raise ValueError(err_message)
        
        logger.info("Successfully logged into cBioPortal and retrieved the JSESSIONID cookie")
        return jsesssion_id
    except BaseException as err:
        logger.error(f"An error occurred while logging into cBioPortal: {err}")
        raise err
    finally:
        await playwright.stop()
