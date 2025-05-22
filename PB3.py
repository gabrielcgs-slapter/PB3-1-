from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium.webdriver.common.keys import Keys
import csv
import datetime
import os
import pytz
import smtplib
import email.message
import psutil
import re
import numpy as np
from dotenv import load_dotenv
import sys
import logging

# --- Logging Configuration ---
# Configure logger first, so it's available for all parts of the script, including env var checks.
LOG_FILE_PATH = "registro.txt"

# Create a logger
logger = logging.getLogger('PB_Scraper')
logger.setLevel(logging.INFO) # Set default logging level for the logger

# Create file handler
file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8') # Append mode
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO) # Log INFO and above to file

# Create stream handler (for console output)
stream_handler = logging.StreamHandler(sys.stdout) # Direct to standard output
stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.INFO) # Show INFO and above on console

# Add handlers to the logger
if not logger.handlers: # Avoid adding handlers multiple times if script is re-run in some contexts
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# Load environment variables from .env file
load_dotenv()
logger.info("Attempting to load environment variables from .env file.")

# --- Environment Variable Configuration ---
# The following environment variables are required to run this script.
# Create a .env file in the same directory as this script with the following format:
#
# DESTINATARIO_EMAIL=your_recipient_email@example.com
# PB_LOGIN=your_pb_login
# PB_SENHA=your_pb_password
# EMAIL_PASSWORD=your_email_password
#
# IMPORTANT: Add .env to your .gitignore file to avoid committing sensitive credentials.

# Retrieve environment variables
destinatario_email = os.environ.get('DESTINATARIO_EMAIL')
pb_login = os.environ.get('PB_LOGIN')
pb_senha = os.environ.get('PB_SENHA')
email_password = os.environ.get('EMAIL_PASSWORD')

# Validate that all required environment variables are set
missing_vars = []
if not destinatario_email:
    missing_vars.append("DESTINATARIO_EMAIL")
if not pb_login:
    missing_vars.append("PB_LOGIN")
if not pb_senha:
    missing_vars.append("PB_SENHA")
if not email_password:
    missing_vars.append("EMAIL_PASSWORD")

if missing_vars:
    error_message = "Error: The following required environment variables are not set: " + ", ".join(missing_vars)
    logger.critical(error_message)
    logger.critical("Please create or update your .env file and try again. Exiting script.")
    # print("Error: The following required environment variables are not set:") # Replaced by logger
    # for var in missing_vars:
    #     print(f"- {var}")
    # print("Please create or update your .env file and try again.")
    sys.exit(1)
else:
    logger.info("All required environment variables are loaded successfully.")


#destinatário = 'gabriel.calazans@ini.fiocruz.br'
destinatário = destinatario_email

# GABRIEL LOGIN
login = pb_login; senha = pb_senha

# TANIA LOGIN
#login = "tania.krstic@ini.fiocruz.br"; senha = "987654"

timezone = pytz.timezone('Etc/GMT+3')

def kill_existing_browser_processes():
    """Kills any existing chromedriver or chrome processes."""
    logger.warning("Attempting to terminate existing 'chrome' and 'chromedriver' processes.")
    killed_any = False
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        if proc.info["name"] in ["chromedriver", "chrome"]:
            try:
                logger.info(f"Attempting to kill process: {proc.info['name']} (PID {proc.info['pid']})")
                proc.kill()
                logger.info(f"Successfully killed process: {proc.info['name']} (PID {proc.info['pid']})")
                killed_any = True
            except psutil.NoSuchProcess:
                logger.warning(f"Process {proc.info['name']} (PID {proc.info['pid']}) not found or already terminated.")
            except psutil.AccessDenied:
                logger.error(f"Access denied when trying to kill process: {proc.info['name']} (PID {proc.info['pid']}). May require higher privileges.")
            except Exception as e:
                logger.error(f"Error killing process {proc.info['name']} (PID {proc.info['pid']}): {e}", exc_info=True)
    if not killed_any:
        logger.info("No 'chrome' or 'chromedriver' processes found running or needing termination.")

def initialize_webdriver():
    """Initializes and returns the Selenium WebDriver and WebDriverWait objects."""
    logger.info("Initializing WebDriver...")
    options = Options()
    #options.add_argument("--disable-gpu")  # Desativa GPU para melhorar desempenho
    options.add_argument("--no-sandbox")  # Evita problemas de permissão
    options.add_argument("--disable-dev-shm-usage")  # Melhora estabilidade
    options.add_argument("--blink-settings=imagesEnabled=false")  # Desativa imagens
    options.add_argument("--disable-extensions")  # Desativa extensões
    options.add_argument("--disable-popup-blocking")  # Evita bloqueios de pop-up
    options.add_argument("--disable-infobars")  # Remove barra de informações do Chrome
    #options.add_argument("--headless")  # Modo headless (opcional)
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 300) # Default wait time of 300 seconds
        logger.info("WebDriver initialized successfully.")
        return driver, wait
    except WebDriverException as e:
        logger.critical(f"WebDriverException during WebDriver initialization: {e}", exc_info=True)
        raise # Re-raise the exception to be caught by main or terminate script
    except Exception as e:
        logger.critical(f"An unexpected error occurred during WebDriver initialization: {e}", exc_info=True)
        raise

data_hora0 = datetime.datetime.now(timezone) # Script start time
data_hora00 = str(data_hora0) # String representation of start time
# print(f"Hora de início: {str(data_hora0)[0:16]}") # Will be logged in main

# Example usage (will be moved to main)
# kill_existing_browser_processes()
# driver, wait = initialize_webdriver()
# driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
# driver.maximize_window()

# print("Abrindo Plataforma Brasil")
# time.sleep(10)

def login_to_plataforma_brasil(driver, wait, login_email, login_password):
    """
    Logs into Plataforma Brasil.
    Returns True on successful login, False otherwise.
    """
    logger.info("Attempting to log in to Plataforma Brasil...")
    try:
        driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
        logger.info(f"Navigated to login page: https://plataformabrasil.saude.gov.br/login.jsf")
        driver.maximize_window()
    except WebDriverException as e:
        logger.error(f"WebDriverException while navigating to login page: {e}", exc_info=True)
        return False # Cannot proceed if navigation fails

    logger.info("Login page opened. Waiting for elements...")
    time.sleep(10) # Initial wait for page to load, consider replacing with explicit wait for a specific element

    login_attempts = 0
    max_login_attempts = 3 # Try to login 3 times before failing

    while login_attempts < max_login_attempts:
        try:
            # Wait for the login button to be clickable
            wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[3]/div/div/form[1]/input[4]')))
            
            # Clear email field and enter email
            email_field = driver.find_element(By.XPATH,'//*[@id="j_id19:email"]')
            email_field.clear()
            email_field.send_keys(login_email)
            
            # Clear password field and enter password
            password_field = driver.find_element(By.XPATH,'//*[@id="j_id19:senha"]')
            password_field.clear()
            password_field.send_keys(login_password)
            
            # Click login button
            driver.find_element(By.XPATH, '//*[@id="j_id19"]/input[4]').click()
            logger.info("Login form submitted.")
            time.sleep(5) # Wait for login process, consider explicit wait for dashboard element
            
            try:   
                # Click to invalidate other logged in user session if modal appears
                invalidate_session_button_xpath = '//*[@id="formModalMsgUsuarioLogado:idBotaoInvalidarUsuarioLogado"]'
                # Using a shorter wait for this optional element
                short_wait = WebDriverWait(driver, 5) 
                invalidate_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, invalidate_session_button_xpath)))
                invalidate_button.click()
                logger.info("Invalidated existing user session by clicking modal button.")
                time.sleep(5) # Wait after invalidating session
            except TimeoutException:
                logger.info("No existing session modal detected or timed out waiting for it (this is often normal).")
                pass # Modal didn't appear or wasn't clickable in time, which is often fine
            except NoSuchElementException:
                logger.info("No existing session modal found (NoSuchElementException - this is often normal).")
                pass

            # Check for successful login message or element indicating successful login
            # The text "Bem vindo(a)" or the presence of a known element on the dashboard can be used.
            # For this script, it checks for "sessão" in a div that appears.
            # XPATH for login status: /html/body/div[2]/div/div[4]/div
            login_status_element_xpath = "/html/body/div[2]/div/div[4]/div" # This XPath might indicate login status or error
            # Wait for either a success indicator or an error message to appear
            # For example, wait for a known element on the dashboard or the login status div
            wait.until(EC.presence_of_element_located((By.XPATH, login_status_element_xpath))) # Wait for the status div
            valid_login_text = driver.find_element(By.XPATH, login_status_element_xpath).text
            
            # More robust check: Presence of a known dashboard element
            # dashboard_element_xpath = "XPATH_OF_A_RELIABLE_DASHBOARD_ELEMENT"
            # if driver.find_elements(By.XPATH, dashboard_element_xpath):
            if "sessão iniciada" in valid_login_text.lower() or "bem vindo" in valid_login_text.lower() or "Painel de Navegação" in driver.page_source: # Added another check
                logger.info("Login realizado com sucesso.")
                time.sleep(10) # Pause after successful login to allow page to fully load or for observation
                return True
            else:
                logger.warning(f"Login attempt {login_attempts + 1}/{max_login_attempts} failed. Status text found: '{valid_login_text}'. Retrying...")
                login_attempts += 1
                if login_attempts < max_login_attempts:
                    logger.info("Re-navigating to login page for retry.")
                    driver.get("https://plataformabrasil.saude.gov.br/login.jsf") 
                    time.sleep(5)

        except TimeoutException as e:
            logger.error(f"Timeout during login attempt {login_attempts + 1}/{max_login_attempts}: {e}", exc_info=True)
            login_attempts += 1
            if login_attempts < max_login_attempts:
                 logger.info("Re-navigating to login page after timeout.")
                 driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
                 time.sleep(5)
        except NoSuchElementException as e:
            logger.error(f"NoSuchElementException during login attempt {login_attempts + 1}/{max_login_attempts}: {e}", exc_info=True)
            login_attempts += 1
            if login_attempts < max_login_attempts:
                 logger.info("Re-navigating to login page after NoSuchElementException.")
                 driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
                 time.sleep(5)
        except WebDriverException as e: # Catch other Selenium-related exceptions
            logger.error(f"WebDriverException during login attempt {login_attempts + 1}/{max_login_attempts}: {e}", exc_info=True)
            login_attempts += 1
            if login_attempts < max_login_attempts:
                 logger.info("Re-navigating to login page after WebDriverException.")
                 driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
                 time.sleep(5)
        except Exception as e: # Catch any other unexpected error
            logger.critical(f"An unexpected error occurred during login attempt {login_attempts + 1}/{max_login_attempts}: {e}", exc_info=True)
            login_attempts += 1 # Still increment attempt, might be recoverable
            if login_attempts < max_login_attempts:
                try:
                    logger.info("Attempting to re-navigate to login page after unexpected error.")
                    driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
                    time.sleep(5)
                except Exception as nav_e:
                    logger.critical(f"Failed to re-navigate after unexpected error: {nav_e}", exc_info=True)
                    # If re-navigation also fails, it's unlikely further attempts will succeed
                    return False 
            
    logger.error("Login failed after multiple attempts.")
    return False

def extract_valid_caaes(driver, wait):
    """
    Navigates through pages and extracts a list of valid CAAE numbers.
    Returns a list of unique CAAE strings.
    """
    logger.info("Starting extraction of valid CAAEs...")
    list_CAAE = []
    
    # Assumes login lands on a page where CAAEs are listed or searchable.
    # If not, navigation to the correct page should happen before calling this.
    # Example: driver.get("URL_OF_CAAE_LISTING_PAGE")
    # wait.until(EC.presence_of_element_located((By.XPATH, "SOME_ELEMENT_ON_LISTING_PAGE")))
    # This might require knowing the URL or a specific element on the CAAE listing page.
    # For now, assumes login lands on a page where CAAEs are listed or searchable.
    
    try:
        pagination_info_element_xpath = "//table[@class='rich-dtascroller-table']"
        logger.info(f"Waiting for pagination info element: {pagination_info_element_xpath}")
        # Increased wait time specifically for this element as it seems crucial
        long_wait = WebDriverWait(driver, 60)
        pagination_element = long_wait.until(EC.presence_of_element_located((By.XPATH, pagination_info_element_xpath)))
        paginas0_text = pagination_element.text
        logger.info(f"Pagination text found: '{paginas0_text}'")
        
        match = re.search(r'de ([\d\.]+) registro\(s\)', paginas0_text)
        if not match:
            logger.error(f"Could not parse total number of records from pagination text: '{paginas0_text}'. Check XPath and page structure.")
            return [] 
        
        total_registros_str = match.group(1).replace('.', '') 
        total_registros = int(total_registros_str)
        paginas = (total_registros -1) // 10 
        logger.info(f"Total records: {total_registros}, Pages to iterate: {paginas + 1}")

    except TimeoutException as e:
        logger.error(f"Timeout waiting for pagination info element. Cannot determine number of pages. {e}", exc_info=True)
        return [] 
    except Exception as e: # Catching other potential errors during pagination info extraction
        logger.error(f"Error extracting pagination info: {e}", exc_info=True)
        return []

    if paginas < 0 : # Handles case where total_registros might be 0
        logger.info("No records found or less than one page of records. No CAAEs to extract from pagination.")
        # Still proceed to check current page for CAAEs, as pagination might be absent for single page
        paginas = 0 # Ensure loop runs once for the current page

    for i in range(paginas + 1): 
        logger.info(f"Processing page {i + 1} of {paginas + 1} for CAAEs...")
        try:
            # It's good practice to re-initialize soup for each page if content is dynamic
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract labels containing CAAEs
            labels = soup.find_all("label")
            found_on_page = 0
            for label in labels:
                if '5262' in label.text: 
                    caae_text = label.text.strip().replace("\n", "")
                    list_CAAE.append(caae_text)
                    # logger.debug(f"Found CAAE: {caae_text} on page {i+1}") # DEBUG level for individual finds
                    found_on_page +=1
            logger.info(f"Found {found_on_page} CAAEs containing '5262' on page {i + 1}.")
            
            if i < paginas: # If not the last page, click next
                original_next_page_xpath = '/html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tfoot/tr/td/div/table/tbody/tr/td[6]'
                logger.info(f"Attempting to click next page button (XPath: {original_next_page_xpath})...")
                # Add specific wait for the next button to be clickable before attempting to click
                wait.until(EC.element_to_be_clickable((By.XPATH, original_next_page_xpath))).click()
                logger.info(f"Clicked next page to go to page {i + 2}.")
                # Wait for page content to update. A small fixed wait or wait for a specific element on new page.
                time.sleep(5) # Consider waiting for a specific element that indicates page load
        except TimeoutException as e:
            logger.error(f"Timeout clicking next page button or specific element on page {i + 1}. Stopping CAAE extraction. {e}", exc_info=True)
            break 
        except NoSuchElementException as e:
            logger.error(f"Next page button not found on page {i + 1}. Stopping CAAE extraction. {e}", exc_info=True)
            break
        except WebDriverException as e:
            logger.error(f"WebDriverException on page {i + 1} while trying to extract/navigate: {e}", exc_info=True)
            break
        except Exception as e: # Catch any other unexpected error during page processing
            logger.error(f"Unexpected error on page {i + 1} during CAAE extraction: {e}", exc_info=True)
            break
                
    unique_caaes = sorted(list(set(list_CAAE))) 
    logger.info(f"Total unique CAAEs extracted: {len(unique_caaes)}")
    if not unique_caaes and paginas >=0 :
        logger.warning("No CAAEs were extracted. Check filter criteria ('5262') and website structure if this is unexpected.")
    return unique_caaes
        # CAAEs seem to be in <label> tags and contain '5262' (INI Fiocruz specific?)
        labels = soup.find_all("label")
        for label in labels:
            if '5262' in label.text: # Filter condition for relevant CAAEs
                list_CAAE.append(label.text.strip().replace("\n", ""))
        
        if i < paginas: # If not the last page, click next
            try:
                # XPATH for '>>' (next page) button: /html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tfoot/tr/td/div/table/tbody/tr/td[6]
                # Using a more robust XPath if possible, e.g., based on title or id
                next_page_button_xpath = "//td/div/table/tbody/tr/td[contains(@onclick, ' पुढील पृष्ठ') or contains(@title, 'Próxima Página') or contains(@title, 'Next Page') or @id = 'formListaProjetosPesquisa:j_id137:last']"
                # The provided XPATH was: /html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tfoot/tr/td/div/table/tbody/tr/td[6]
                # It's better to use a more specific one if available. The one above is a guess.
                # For now, using the original one, but it's fragile.
                original_next_page_xpath = '/html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tfoot/tr/td/div/table/tbody/tr/td[6]'
                print("Waiting for next page button...")
                wait.until(EC.element_to_be_clickable((By.XPATH, original_next_page_xpath))).click()
                print("Clicked next page.")
                time.sleep(5) # Wait for page to load
            except TimeoutException:
                print(f"Timeout waiting for next page button on page {i + 1}. Stopping CAAE extraction.")
                break # Stop if next button is not found
            except Exception as e:
                print(f"Error clicking next page on page {i + 1}: {e}. Stopping CAAE extraction.")
                break
                
    unique_caaes = sorted(list(set(list_CAAE))) # Get unique CAAEs and sort them
    print(f"CAAEs válidos extraídos: {len(unique_caaes)}")
    return unique_caaes

CAAE = [] # Will be populated by extract_valid_caaes

# XPaths for process_caae_details (Consider moving to constants at the top)
CAAE_SEARCH_INPUT_XPATH = '/html/body/div[2]/div/div[6]/div[1]/form/div[2]/div[2]/table[1]/tbody/tr/td[2]/table/tbody/tr[2]/td/input'
LUPA_ICON_XPATH = '/html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tbody/tr/td[10]/a/img' # This is likely page dependent, might need adjustment
VOLTAR_AO_MENU_BUTTON_XPATH = '/html/body/div[2]/div/div[3]/div[2]/form/a[2]' # Button to go back after viewing details
# URL for the main page listing projects, to navigate back to after processing a CAAE or if an error occurs during detail processing.
# This needs to be the actual URL from the website.
# Example: PLATAFORMA_BRASIL_MAIN_LIST_URL = "https://plataformabrasil.saude.gov.br/listaprojetos.jsf" (This URL is a guess)


def process_caae_details(driver, wait, caae_number, timezone_obj):
    """
    Processes a single CAAE number to extract its details.
    Returns a dictionary with CAAE details or None if processing fails.
    """
    logger.info(f"Starting to process CAAE: {caae_number}...")
    max_retries = 3
    retry_count = 0
    
    # It's crucial to know the URL of the page where CAAE search can be performed.
    # This helps in recovering from errors by navigating back to a known state.
    # Example: caae_search_page_url = "https://plataformabrasil.saude.gov.br/listaprojetos.jsf" # Replace with actual URL

    while retry_count < max_retries:
        try:
            t1 = datetime.datetime.now(timezone_obj)

            # Ensure driver is on the correct page to search for CAAE
            # If not, navigate to the search page. This is a basic check.
            # A more robust check would be to verify presence of search input, if not, navigate.
            # if caae_search_page_url not in driver.current_url: # Simplified check
            #    driver.get(caae_search_page_url)
            #    wait.until(EC.presence_of_element_located((By.XPATH, CAAE_SEARCH_INPUT_XPATH)))

            # Ensure driver is on the CAAE search/listing page before attempting search
            # This might involve a check of current_url or presence of a known element
            # Example: if "expected_search_page_url_part" not in driver.current_url:
            #    logger.info("Not on CAAE search page, navigating...")
            #    driver.get(ACTUAL_CAAE_SEARCH_PAGE_URL)
            #    wait.until(EC.presence_of_element_located((By.XPATH, CAAE_SEARCH_INPUT_XPATH)))

            search_input = wait.until(EC.presence_of_element_located((By.XPATH, CAAE_SEARCH_INPUT_XPATH)))
            search_input.clear()
            search_input.send_keys(caae_number)
            search_input.send_keys(Keys.ENTER) 
            logger.info(f"Submitted search for CAAE: {caae_number}")
            time.sleep(3) # Wait for search results

            # Click on the "lupa" (magnifying glass) icon to view details
            lupa_attempts = 0
            max_lupa_attempts = 5
            lupa_clicked = False
            while lupa_attempts < max_lupa_attempts:
                try:
                    lupa_icon = wait.until(EC.element_to_be_clickable((By.XPATH, LUPA_ICON_XPATH)))
                    lupa_icon.click()
                    lupa_clicked = True
                    logger.info(f"Lupa icon clicked for CAAE {caae_number}.")
                    break
                except TimeoutException:
                    lupa_attempts += 1
                    logger.warning(f"Lupa icon for CAAE {caae_number} not clickable or found, attempt {lupa_attempts}/{max_lupa_attempts}. Retrying after short wait...")
                    time.sleep(3) 
            
            if not lupa_clicked:
                logger.error(f"Failed to click Lupa icon for CAAE {caae_number} after {max_lupa_attempts} attempts.")
                # This is a significant failure for this CAAE, so we raise an exception to be caught by the outer try-except
                raise TimeoutException(f"Lupa icon not found or clickable for {caae_number} after {max_lupa_attempts} attempts.")

            logger.info(f"Waiting for details page of CAAE {caae_number} to load...")
            time.sleep(5) # Wait for details page to load. Consider explicit wait for a specific detail element.

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            logger.info(f"Page source parsed for CAAE {caae_number}.")

            # Extract study name - td with class "text-top"
            nome_estudo_td = soup.find('td', class_="text-top")
            nome_estudo = nome_estudo_td.text[21:].replace('"',"").strip() if nome_estudo_td else "Nome do estudo não encontrado"
            
            # Extract PI - This is very fragile based on td index.
            # It's better to find a label "Pesquisador Principal:" and get the next td's text.
            all_tds = soup.find_all("td")
            pi_text = "Pesquisador Principal não encontrado"
            # Attempt to find PI more reliably - this is still a guess without seeing the HTML structure
            # for idx, td_element in enumerate(all_tds):
            #     if "pesquisador principal" in td_element.text.lower(): # Check for label
            #         if idx + 1 < len(all_tds): # Check if next td exists
            #             pi_text = all_tds[idx+1].text.replace("\n", "").strip()
            #             break
            if len(all_tds) > 6: # Fallback to original fragile logic if label search fails
                pi_text = all_tds[6].text.replace("\n", "").strip()


            # Extract trámite table - by id 'formDetalharProjeto:tableTramiteApreciacaoProjeto:tb'
            tramite_table_body = soup.find(id='formDetalharProjeto:tableTramiteApreciacaoProjeto:tb')
            tabela_tramites_html = "Tabela de trâmites não encontrada."
            if tramite_table_body:
                spans = tramite_table_body.find_all('span')
                b = [span.text.strip() for span in spans] # Clean up text from spans
                q_rows = []
                if len(b) >= 8 : # Ensure there are spans to process, assuming 8 items per row
                    for x_row in range(len(b) // 8):
                        row_data = b[x_row*8 : (x_row+1)*8]
                        q_rows.append(f"""
                            <tr>
                            <th>{x_row+1}</th> 
                            <td>{row_data[0]}</td><td>{row_data[1]}</td><td>{row_data[2]}</td><td>{row_data[3]}</td>
                            <td>{row_data[4]}</td><td>{row_data[5]}</td><td>{row_data[6]}</td><td>{row_data[7]}</td>
                            </tr>
                        """)
                    output_html_rows = ''.join(q_rows)
                    tabela_tramites_html = f"""
                                    <table border="1" class="dataframe" style="text-align: center"> 
                                    <thead><tr> 
                                    <th>#</th><th>Apreciação</th><th>Data/Hora</th><th>Tipo Trâmite</th><th>Versão</th> 
                                    <th>Perfil</th><th>Origem</th><th>Destino</th><th>Informações</th> 
                                    </tr></thead> 
                                    <tbody>{output_html_rows}</tbody> 
                                    </table>
                                    """

            # Extract CAAE from details page for confirmation - also fragile by td index
            caae_estudo_confirmacao = "CAAE não encontrado na página de detalhes"
            # Similar to PI, try to find a label "CAAE:" and get the next td's text.
            # for idx, td_element in enumerate(all_tds):
            #    if "caae:" in td_element.text.lower():
            #        if idx + 1 < len(all_tds):
            #            caae_estudo_confirmacao = all_tds[idx+1].text.replace("\n", "").strip()
            #            break
            if len(all_tds) > 15: # Fallback
                 caae_estudo_confirmacao = all_tds[15].text.replace("\n", "").replace("CAAE: ","").strip()


            corpo_email_html_fragment = f"""
                                        <div class="study-details">
                                        <p><b>Título do Estudo:</b> {nome_estudo}</p> 
                                        <p><b>CAAE:</b> {caae_estudo_confirmacao}</p> 
                                        <p><b>Pesquisador Principal:</b> {pi_text}</p> 
                                        <p><b>Histórico de Trâmites:</b></p>
                                        {tabela_tramites_html}
                                        </div>
                                        """
            
            # Navigate back to the search/listing page
            wait.until(EC.element_to_be_clickable((By.XPATH, VOLTAR_AO_MENU_BUTTON_XPATH))).click()
            logger.info(f"Returned to menu/listing page after processing CAAE {caae_number}.")
            time.sleep(3) # Wait for menu page to load

            t2 = datetime.datetime.now(timezone_obj)
            processing_time = t2 - t1
            logger.info(f"Successfully processed CAAE: {caae_number} in {processing_time}.")
            
            return {
                'caae': caae_number, 
                'email_html': corpo_email_html_fragment, 
                'processing_time': processing_time
            }
        except TimeoutException as e: # More specific exception
            retry_count += 1
            logger.warning(f"Timeout processing CAAE {caae_number}: {e}. Attempt {retry_count}/{max_retries}.", exc_info=True)
        except NoSuchElementException as e: # More specific exception
            retry_count += 1
            logger.warning(f"NoSuchElementException for CAAE {caae_number}: {e}. Attempt {retry_count}/{max_retries}.", exc_info=True)
        except WebDriverException as e: # More specific exception for other browser/driver issues
            retry_count += 1
            logger.warning(f"WebDriverException for CAAE {caae_number}: {e}. Attempt {retry_count}/{max_retries}.", exc_info=True)
        except Exception as e: # Catch-all for other unexpected errors during CAAE processing
            retry_count += 1
            logger.error(f"Unexpected error processing CAAE {caae_number}: {e}. Attempt {retry_count}/{max_retries}.", exc_info=True)
        
        # Common recovery attempt for retries
        if retry_count < max_retries:
            try:
                logger.info(f"Attempting to navigate back to menu/listing page for CAAE {caae_number} before retry.")
                # Check if on details page before clicking back, otherwise, might be on search page already
                if "DetalheDoProjeto" in driver.current_url: # A guess for detail page URL fragment
                     wait.until(EC.element_to_be_clickable((By.XPATH, VOLTAR_AO_MENU_BUTTON_XPATH))).click()
                # Else, assume already on a list/search page or recovery handled by main loop's navigation
                time.sleep(5) 
            except Exception as nav_e:
                logger.error(f"Critical: Failed to navigate after error processing CAAE {caae_number} during retry attempt: {nav_e}. WebDriver state might be unstable.", exc_info=True)
                # If navigation recovery fails, further retries for this CAAE are unlikely to succeed
                break # Break from the retry loop for this CAAE
            
    logger.error(f"Failed to process CAAE {caae_number} after {max_retries} attempts.")
    return None # Indicate failure for this CAAE

def compare_with_previous_run(current_data_df, old_csv_path="old.csv", new_csv_path="new.csv"):
    """
    Compares the current run's data with the previous run's data.
    Saves current data, manages old/new CSV files.
    Returns a tuple: (list of HTML strings for updated studies, count of updated studies).
    """
    logger.info("Starting comparison with previous run data...")
    if 'caae' not in current_data_df.columns or 'email_html' not in current_data_df.columns:
        logger.error("Error: current_data_df for comparison must contain 'caae' and 'email_html' columns.")
        return [], 0
        
    # --- File I/O Operations ---
    try:
        if os.path.exists(new_csv_path):
            if os.path.exists(old_csv_path):
                os.remove(old_csv_path)
                logger.info(f"Removed old data file: '{old_csv_path}'.")
            os.rename(new_csv_path, old_csv_path)
            logger.info(f"Renamed current data file '{new_csv_path}' to '{old_csv_path}'.")
    except OSError as e:
        logger.error(f"OSError managing CSV files: {e}. Proceeding by saving new data; comparison might be affected if old file was not correctly moved.", exc_info=True)

    try:
        current_data_df.to_csv(new_csv_path, index=False)
        logger.info(f"Saved current run data to '{new_csv_path}'.")
    except Exception as e:
        logger.error(f"Failed to save current data to '{new_csv_path}': {e}", exc_info=True)
        # If we can't save the new data, the function should probably indicate a problem.
        # However, for now, it attempts to proceed with comparison if old data exists.

    # --- Load Old Data and Perform Comparison ---
    if not os.path.exists(old_csv_path):
        logger.warning(f"'{old_csv_path}' not found. Assuming first run or no previous data for comparison.")
        # All items in current_data_df are considered new/updated.
        updated_caae_html_list = current_data_df['email_html'].tolist()
        num_updated_studies = len(updated_caae_html_list)
        logger.info(f"No previous data; {num_updated_studies} studies from current run will be reported as new/updated.")
        return updated_caae_html_list, num_updated_studies

    try:
        old_df = pd.read_csv(old_csv_path)
        logger.info(f"Successfully loaded previous data from '{old_csv_path}'.")
    except Exception as e:
        logger.error(f"Failed to load previous data from '{old_csv_path}': {e}. All current items will be treated as new.", exc_info=True)
        updated_caae_html_list = current_data_df['email_html'].tolist()
        num_updated_studies = len(updated_caae_html_list)
        return updated_caae_html_list, num_updated_studies
        
    return _perform_data_comparison(current_data_df, old_df)

def _perform_data_comparison(new_df, old_df):
    """
    Core logic to compare two DataFrames (new_df and old_df).
    Returns a tuple: (list of HTML strings for updated/new studies, count of updated/new studies).
    Assumes 'caae' and 'email_html' columns exist.
    """
    logger.info("Performing core data comparison...")
    # Merge current and old dataframes
    comparison_df = pd.merge(
        new_df,
        old_df,
        on='caae', # Key for comparison
        how='outer', # Keep all CAAEs from both dataframes
        suffixes=('_new', '_old')
    )

    # Identify updated studies:
    # 1. Content changed: 'email_html_new' is different from 'email_html_old'.
    # 2. New CAAE: 'email_html_new' is present, but 'email_html_old' is NaN.
    # We are not explicitly flagging removed CAAEs (present in old, NaN in new) for email notification,
    # but they are part of the comparison_df if `how='outer'` is used.
    
    # Condition for changed content (present in both, but different email_html)
    content_changed_mask = (comparison_df['email_html_new'].notna() & 
                            comparison_df['email_html_old'].notna() & 
                            (comparison_df['email_html_new'] != comparison_df['email_html_old']))
    
    # Condition for new CAAEs (present in new_df, not in old_df)
    new_caae_mask = comparison_df['email_html_new'].notna() & comparison_df['email_html_old'].isna()
    
    # Combine masks: interested in content changed OR new CAAEs
    # These are the rows whose 'email_html_new' will be included in the notification.
    updated_studies_df = comparison_df[content_changed_mask | new_caae_mask]

    updated_caae_html_list = updated_studies_df['email_html_new'].tolist() 
    num_updated_studies = len(updated_caae_html_list)

    logger.info(f"Core comparison complete. Found {num_updated_studies} updated or new studies for notification.")
    return updated_caae_html_list, num_updated_studies

def send_notification_email(recipient_email, email_app_password, num_updates, email_body_updates_html, script_start_time_obj, timezone_obj, sender_email_address="regulatorios.aids@gmail.com"):
    """
    Constructs and sends a notification email with updates.
    Uses a predefined sender email, but this could be an environment variable.
    """
    logger.info(f"Preparing to send email to {recipient_email} for {num_updates} updates...")
    
    current_time = datetime.datetime.now(timezone_obj)
    duration = current_time - script_start_time_obj # Duration of the script until this point
    email_date_str = current_time.strftime('%d/%m/%Y')
    current_datetime_str_for_email = current_time.strftime("%d/%m/%Y %H:%M:%S")

    email_subject = f'Atualizações da Plataforma Brasil em {email_date_str}'
    
    full_email_body = f"""
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .study-details {{ border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <p>Bom dia equipe,</p> 
        <p>Abaixo os estudos que tiveram atualizações ou são novos na Plataforma Brasil no dia {email_date_str}.</p> 
        <p>Houve alteração ou inclusão em <b>{num_updates}</b> estudos.</p> 
        <br/> 
        {email_body_updates_html}
        <br/> 
        <p>Este e-mail foi gerado automaticamente.</p>
        <p>Hora do envio: {current_datetime_str_for_email}. Duração da execução do script: {str(duration).split('.')[0]}.</p>
        <p>Um ótimo dia a todos e todas!</p>
    </body>
    </html>
    """

    msg = email.message.Message()
    msg['Subject'] = email_subject
    msg['From'] = sender_email_address
    msg['To'] = recipient_email
    
    msg.add_header('Content-Type', 'text/html; charset=utf-8')
    msg.set_payload(full_email_body.encode('utf-8'))

    try:
        if not email_app_password:
            logger.error("Email app password is not set (EMAIL_PASSWORD environment variable). Cannot send email.")
            return False
            
        logger.info(f"Connecting to SMTP server: smtp.gmail.com:587 for sender {sender_email_address}")
        s = smtplib.SMTP('smtp.gmail.com: 587')
        s.starttls()
        logger.info(f"Logging into SMTP server as {sender_email_address}.")
        s.login(msg['From'], email_app_password)
        logger.info(f"Sending email to {recipient_email}.")
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
        logger.info("Email sent successfully.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error for sender {sender_email_address}: {e}. Check email/password or app password settings.", exc_info=True)
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server disconnected: {e}", exc_info=True)
        return False
    except smtplib.SMTPException as e: # Catch other SMTPlib specific errors
        logger.error(f"SMTPException while sending email: {e}", exc_info=True)
        return False
    except Exception as e: # Catch any other unexpected error during email sending
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        return False

# def log_script_run(...): # This function is removed. Logging is done directly.

# --- Main script execution logic ---
def main():
    """
    Main function to orchestrate the script execution.
    """
    global data_hora0, data_hora00, timezone, pb_login, pb_senha, destinatario_email, email_password, logger

    # Script start time is already set (data_hora0, data_hora00)
    # Log script start
    logger.info(f"--- Iniciando script PB3 --- Hora de início: {data_hora0.strftime('%d/%m/%Y %H:%M:%S')} ---")

    kill_existing_browser_processes() # Uses logger internally
    driver, wait = None, None 

    try:
        driver, wait = initialize_webdriver() # Uses logger internally

        if not login_to_plataforma_brasil(driver, wait, pb_login, pb_senha): # Uses logger
            logger.critical("Falha no login. Encerrando o script.")
            # No need for explicit log_script_run call here, main's finally block will log end.
            return 

        caae_list_extracted = extract_valid_caaes(driver, wait) # Uses logger
        if not caae_list_extracted:
            logger.warning("Nenhum CAAE extraído. Verifique a plataforma ou os filtros. Encerrando.")
            return

        processed_caaes_data = []
        logger.info(f"Iniciando processamento de {len(caae_list_extracted)} CAAEs...")
        for count, caae_s_num in enumerate(caae_list_extracted):
            logger.info(f"Processando CAAE {count + 1}/{len(caae_list_extracted)}: {caae_s_num}")
            details = process_caae_details(driver, wait, caae_s_num, timezone) # Uses logger
            if details:
                processed_caaes_data.append(details)
            else:
                logger.error(f"Falha ao processar detalhes para o CAAE: {caae_s_num}. Detalhes não serão incluídos.")
        
        logger.info("Processamento de todos os CAAEs concluído.")

        if not processed_caaes_data:
            logger.warning("Nenhum dado de CAAE foi processado com sucesso. Não há o que comparar ou enviar por email.")
            return

        current_run_df = pd.DataFrame(processed_caaes_data)
        if 'caae' not in current_run_df.columns or 'email_html' not in current_run_df.columns:
             logger.critical("Erro crítico: DataFrame de CAAEs processados não contém as colunas 'caae' ou 'email_html'. Não é possível continuar.")
             return

        updated_html_fragments_list, num_updated_total = compare_with_previous_run(current_run_df) # Uses logger

        email_final_status_message = "Nenhuma atualização encontrada ou erro na comparação, email não enviado."
        if num_updated_total > 0:
            logger.info(f"Encontradas {num_updated_total} atualizações/novos estudos. Preparando email...")
            complete_email_body_html = "<br/><hr/><br/>".join(updated_html_fragments_list) 
            
            email_sent_successfully = send_notification_email( # Uses logger
                recipient_email=destinatario_email,
                email_app_password=email_password, 
                num_updates=num_updated_total,
                email_body_updates_html=complete_email_body_html,
                script_start_time_obj=data_hora0, # Pass the actual start time object
                timezone_obj=timezone
            )
            if email_sent_successfully:
                email_final_status_message = f"Email enviado com sucesso para {destinatario_email} com {num_updated_total} atualizações/novos estudos."
                logger.info(email_final_status_message)
            else:
                email_final_status_message = f"Falha ao enviar email para {destinatario_email} com {num_updated_total} atualizações/novos estudos."
                logger.error(email_final_status_message)
        else:
            logger.info("Nenhuma atualização ou novo estudo encontrado após comparação. Email não será enviado.")
            email_final_status_message = "Nenhuma atualização ou novo estudo encontrado, email não enviado."
        
        # Information for final log message in `finally` block will be set here
        # This replaces parts of the old log_script_run function.
        main.num_updates = num_updated_total 
        main.email_status = email_final_status_message

    except Exception as e: # Catch any unexpected error in main workflow
        logger.critical(f"Erro crítico inesperado na função main(): {e}", exc_info=True)
        main.num_updates = 0 # Ensure these exist for the finally block
        main.email_status = f"Script encerrado prematuramente devido a erro crítico: {e}"
    finally:
        if driver:
            logger.info("Fechando WebDriver.")
            try:
                driver.quit()
                logger.info("WebDriver fechado com sucesso.")
            except WebDriverException as e:
                logger.error(f"WebDriverException ao tentar fechar o WebDriver: {e}", exc_info=True)

        script_end_time = datetime.datetime.now(timezone)
        total_duration = script_end_time - data_hora0 # data_hora0 is the script start time
        
        # Retrieve status from main function attributes, or set defaults if error occurred before they were set
        num_final_updates = getattr(main, 'num_updates', 0)
        email_final_status = getattr(main, 'email_status', "Status do email não determinado devido a erro.")

        logger.info(f"--- Script PB3 concluído --- Hora de término: {script_end_time.strftime('%d/%m/%Y %H:%M:%S')} ---")
        logger.info(f"Tempo total de execução: {str(total_duration).split('.')[0]}")
        logger.info(f"Número de estudos atualizados/novos: {num_final_updates}")
        logger.info(f"Status final do Email: {email_final_status}")
        
        # Close logger handlers to flush and release file
        # This is important especially for file handler
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


if __name__ == "__main__":
    if not missing_vars: 
        main()
    else:
        # Critical log for missing env vars already happened.
        # This message is for console if script somehow proceeds or for clarity.
        # logger might not be fully configured if this is hit very early, so print is a fallback.
        fallback_msg = "Script não pode iniciar devido a variáveis de ambiente ausentes (verifique o início do log)."
        if logger.handlers: # Check if logger has handlers (i.e., configured)
            logger.critical(fallback_msg)
        else:
            print(f"CRITICAL: {fallback_msg}")