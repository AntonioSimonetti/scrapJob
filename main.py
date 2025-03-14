"""
from playwright.sync_api import sync_playwright
import time
import json
import random

from api_client import send_jobs_to_analysis
from config.credentials import EMAIL, PASSWORD, TIME_FILTERS
from utils.file_handler import load_container_class, save_container_class, save_fetched_links, load_fetched_links
from utils.browser_utils import verify_container_class, check_login, perform_login
from utils.signal_handler import setup_signal_handling, keep_running
from dynamicClassFinder import find_scrollable_container

playwright = None
browser = None

# Lista di User Agents per la rotazione
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78",
]

def scroll_job_container(page, container_class):
    print("📜 Eseguo lo scrolling del container dei job card...")
    container_selector = f".{container_class}"
    # Ottieni inizialmente la lista dei job card
    prev_count = 0
    while True:
        job_cards = page.query_selector_all(f"{container_selector} .job-card-container__link")
        current_count = len(job_cards)
        print(f"   Job card trovati finora: {current_count}")
        if current_count > prev_count:
            prev_count = current_count
            # Scrolla ulteriormente il container (scorrimento di 300 px, per esempio)
            page.evaluate(f"""
""""
                () => {{
                    const container = document.querySelector('{container_selector}');
                    if (container) {{
                        container.scrollBy(0, 300);
                    }}
                }}
            """
""")
            time.sleep(2)
        else:
            break
    print(f"   Numero finale di job card: {current_count}")
    return job_cards

def scrape_job_card(page, job_card):
    try:
        job_card.click()
        print("✅ Job card cliccato, attendo aggiornamento pannello...")
        time.sleep(3)
        # Controlla se compare il modale di login
        login_modal = page.query_selector(".sign-in-modal__screen")
        if login_modal and login_modal.is_visible():
            print("⚠️ Modale di login rilevato durante la visualizzazione del job card!")
            username_input = page.query_selector("input#base-sign-in-modal_session_key, input#username")
            if username_input and username_input.is_visible():
                print("Compilazione del campo username...")
                username_input.fill(EMAIL)
            else:
                print("Campo username non visibile; presumibilmente precompilato.")
            password_input = page.query_selector("input#base-sign-in-modal_session_password, input#password")
            if password_input and password_input.is_visible():
                print("Compilazione del campo password...")
                password_input.fill(PASSWORD)
            else:
                print("Campo password non trovato!")
            login_button = page.query_selector("button[data-id='sign-in-form__submit-btn']")
            if login_button:
                login_button.click()
                print("⏳ Effettuando il login dal modale...")
                time.sleep(5)
                # Dopo il login, clicca nuovamente il job card per aggiornare il pannello
                job_card.click()
                time.sleep(3)
        
        # Estrai il link dalla job card (assumendo che abbia l'attributo href)
        link = job_card.get_attribute("href")
        if not link:
            link = page.url
        
        # Estrai il contenuto dal pannello dei dettagli, ad es. da un elemento con id "job-details"
        details = page.query_selector("#job-details")
        content = details.inner_text() if details else ""
        
        return {"url": f"https://www.linkedin.com{link}" if not link.startswith("http") else link,
                "content": content}
    except Exception as e:
        print(f"⚠️ Errore nello scraping del job card: {e}")
        return {"url": "", "content": f"Error: {str(e)}"}

def process_jobs_on_the_fly():
    global browser, playwright
    jobs_data = []
    processed_links = set()
    
    user_agent = random.choice(USER_AGENTS)
    print(f"🔄 Utilizzando User Agent: {user_agent}")
    if browser:
        browser.close()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="./playwright_data",
        headless=False,
        user_agent=user_agent
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Assicurati di essere loggato
    page.goto("https://www.linkedin.com")
    time.sleep(3)
    if not check_login(page):
        perform_login(page, EMAIL, PASSWORD)
        time.sleep(5)
    
    # Naviga alla pagina di ricerca
    time_param = TIME_FILTERS.get("24h", "r86400")
    search_url = f"https://www.linkedin.com/jobs/search/?keywords=Developer&location=Italy&f_TPR={time_param}"
    page.goto(search_url)
    time.sleep(5)
    
    # Ottieni (o verifica) la container class per lo scrolling
    container_class = load_container_class()
    if not verify_container_class(page, container_class):
        print("⚠️ Saved container class non funzionante, trovo una nuova...")
        container_class = find_scrollable_container(page)
        if container_class:
            save_container_class(container_class)
        else:
            print("❌ Nessun container scrollabile trovato!")
            return []
    print(f"\n🎯 Uso container class: .{container_class}")
    
    while True:
        # Scrolla il container per caricare tutti i job card
        job_cards = scroll_job_container(page, container_class)
        print(f"🔍 Trovati {len(job_cards)} job card nella pagina corrente.")
        
        if not job_cards or len(job_cards) == 0:
            print("⚠️ Nessun job card trovato, esco dal ciclo.")
            break
        
        # Processa ogni job card che non è già stato processato
        for job in job_cards:
            link = job.get_attribute("href")
            if link in processed_links:
                continue
            job_data = scrape_job_card(page, job)
            processed_links.add(link)
            jobs_data.append(job_data)
            time.sleep(1)
          
            # Esci subito se abbiamo raccolto 25 offerte
            if len(jobs_data) >= 25:
                print("Raggiunto il numero target di 25 offerte, esco dal ciclo.")
                break
        
        # Se abbiamo già 25 offerte, esci dall'intero ciclo
        if len(jobs_data) >= 25:
            break

        # Gestione della paginazione
        pagination_list = page.query_selector('ul.artdeco-pagination__pages')
        if pagination_list:
            current_page_button = page.query_selector('button[aria-current="true"]')
            current_page_num = int(current_page_button.query_selector("span").inner_text())
            page_buttons = page.query_selector_all('[data-test-pagination-page-btn]')
            total_pages = len(page_buttons)
            print(f"📖 Pagina {current_page_num} di {total_pages}")
            if current_page_num < total_pages:
                next_page_btn = page.query_selector(f'[data-test-pagination-page-btn="{current_page_num + 1}"]')
                if next_page_btn:
                    next_page_btn.click()
                    time.sleep(5)
                    continue
                else:
                    print("⚠️ Pulsante per la pagina successiva non trovato.")
                    break
            else:
                print("🏁 Raggiunta l'ultima pagina.")
                break
        else:
            print("🏁 Nessuna paginazione trovata, esco dal ciclo.")
            break
    
    page.close()
    return jobs_data

def scrape_linkedin_jobs(query="Junior Developer", location="Italy", max_results=200, time_filter="24h"):
    print("🚀 Avvio dello scraping on the fly di LinkedIn jobs...")
    
    jobs_data = process_jobs_on_the_fly()
    jobs_data = jobs_data[:max_results]
    return jobs_data

if __name__ == "__main__":
    setup_signal_handling()
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="./playwright_data",
        headless=False
    )
    
    try:
        results = scrape_linkedin_jobs(query="Junior Java Developer", location="Italy", time_filter="24h")
        
        if results:
            print("\n🔽 RISULTATI FINALI JSON:")
            print(f"Trovati {len(results)} annunci di lavoro con contenuto")
            # Stampa il JSON formattato per controllare il contenuto
            # print(json.dumps(results, indent=2, ensure_ascii=False))
            
            with open('job_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print("💾 Risultati salvati in job_results.json")
            
            print("\n📤 Invio dati all'analisi AI...")
            send_jobs_to_analysis(results)
        else:
            print("❌ Nessun risultato da inviare all'analisi.")
    
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
    
    finally:
        keep_running()
"""

from playwright.sync_api import sync_playwright
import time
import json
import random

from api_client import send_jobs_to_analysis
from config.credentials import EMAIL, PASSWORD, TIME_FILTERS
from utils.file_handler import load_container_class, save_container_class, save_fetched_links, load_fetched_links
from utils.browser_utils import verify_container_class, check_login, perform_login
from utils.signal_handler import setup_signal_handling, keep_running
from dynamicClassFinder import find_scrollable_container

playwright = None
browser = None

# Lista di User Agents per la rotazione
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78",
]

def scroll_job_container(page, container_class):
    print("📜 Eseguo lo scrolling del container dei job card...")
    container_selector = f".{container_class}"
    # Ottieni inizialmente la lista dei job card
    prev_count = 0
    while True:
        job_cards = page.query_selector_all(f"{container_selector} .job-card-container__link")
        current_count = len(job_cards)
        print(f"   Job card trovati finora: {current_count}")
        if current_count > prev_count:
            prev_count = current_count
            # Scrolla ulteriormente il container (scorrimento di 300 px, per esempio)
            page.evaluate(f"""
                () => {{
                    const container = document.querySelector('{container_selector}');
                    if (container) {{
                        container.scrollBy(0, 300);
                    }}
                }}
            """)
            time.sleep(2)
        else:
            break
    print(f"   Numero finale di job card: {current_count}")
    return job_cards

def scrape_job_card(page, job_card):
    try:
        job_card.click()
        print("✅ Job card cliccato, attendo aggiornamento pannello...")
        time.sleep(3)
        # Controlla se compare il modale di login
        login_modal = page.query_selector(".sign-in-modal__screen")
        if login_modal and login_modal.is_visible():
            print("⚠️ Modale di login rilevato durante la visualizzazione del job card!")
            username_input = page.query_selector("input#base-sign-in-modal_session_key, input#username")
            if username_input and username_input.is_visible():
                print("Compilazione del campo username...")
                username_input.fill(EMAIL)
            else:
                print("Campo username non visibile; presumibilmente precompilato.")
            password_input = page.query_selector("input#base-sign-in-modal_session_password, input#password")
            if password_input and password_input.is_visible():
                print("Compilazione del campo password...")
                password_input.fill(PASSWORD)
            else:
                print("Campo password non trovato!")
            login_button = page.query_selector("button[data-id='sign-in-form__submit-btn']")
            if login_button:
                login_button.click()
                print("⏳ Effettuando il login dal modale...")
                time.sleep(5)
                # Dopo il login, clicca nuovamente il job card per aggiornare il pannello
                job_card.click()
                time.sleep(3)
        
        # Estrai il link dalla job card (assumendo che abbia l'attributo href)
        link = job_card.get_attribute("href")
        if not link:
            link = page.url
        
        # Estrai il contenuto dal pannello dei dettagli, ad es. da un elemento con id "job-details"
        details = page.query_selector("#job-details")
        content = details.inner_text() if details else ""
        
        return {"url": f"https://www.linkedin.com{link}" if not link.startswith("http") else link,
                "content": content}
    except Exception as e:
        print(f"⚠️ Errore nello scraping del job card: {e}")
        return {"url": "", "content": f"Error: {str(e)}"}

def process_jobs_on_the_fly(search_url):
    global browser, playwright
    jobs_data = []
    processed_links = set()
    
    user_agent = random.choice(USER_AGENTS)
    print(f"🔄 Utilizzando User Agent: {user_agent}")
    if browser:
        browser.close()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="./playwright_data",
        headless=False,
        user_agent=user_agent
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Assicurati di essere loggato
    page.goto("https://www.linkedin.com")
    time.sleep(3)
    if not check_login(page):
        perform_login(page, EMAIL, PASSWORD)
        time.sleep(5)
    
    # Naviga alla pagina di ricerca
    page.goto(search_url)
    time.sleep(5)
    
    # Ottieni (o verifica) la container class per lo scrolling
    container_class = load_container_class()
    if not verify_container_class(page, container_class):
        print("⚠️ Saved container class non funzionante, trovo una nuova...")
        container_class = find_scrollable_container(page)
        if container_class:
            save_container_class(container_class)
        else:
            print("❌ Nessun container scrollabile trovato!")
            return []
    print(f"\n🎯 Uso container class: .{container_class}")
    
    while True:
        # Scrolla il container per caricare tutti i job card
        job_cards = scroll_job_container(page, container_class)
        print(f"🔍 Trovati {len(job_cards)} job card nella pagina corrente.")
        
        if not job_cards or len(job_cards) == 0:
            print("⚠️ Nessun job card trovato, esco dal ciclo.")
            break
        
        # Processa ogni job card che non è già stato processato
        for job in job_cards:
            link = job.get_attribute("href")
            if link in processed_links:
                continue
            job_data = scrape_job_card(page, job)
            processed_links.add(link)
            jobs_data.append(job_data)
            time.sleep(1)
          
            # Esci subito se abbiamo raccolto 25 offerte
            if len(jobs_data) >= 25:
                print("Raggiunto il numero target di 25 offerte, esco dal ciclo.")
                break
        
        # Se abbiamo già 25 offerte, esci dall'intero ciclo
        if len(jobs_data) >= 25:
            break

        # Gestione della paginazione
        pagination_list = page.query_selector('ul.artdeco-pagination__pages')
        if pagination_list:
            current_page_button = page.query_selector('button[aria-current="true"]')
            current_page_num = int(current_page_button.query_selector("span").inner_text())
            page_buttons = page.query_selector_all('[data-test-pagination-page-btn]')
            total_pages = len(page_buttons)
            print(f"📖 Pagina {current_page_num} di {total_pages}")
            if current_page_num < total_pages:
                next_page_btn = page.query_selector(f'[data-test-pagination-page-btn="{current_page_num + 1}"]')
                if next_page_btn:
                    next_page_btn.click()
                    time.sleep(5)
                    continue
                else:
                    print("⚠️ Pulsante per la pagina successiva non trovato.")
                    break
            else:
                print("🏁 Raggiunta l'ultima pagina.")
                break
        else:
            print("🏁 Nessuna paginazione trovata, esco dal ciclo.")
            break
    
    page.close()
    return jobs_data

def scrape_linkedin_jobs(query="Junior Developer", location="Italy", max_results=200, time_filter="24h"):
    print("🚀 Avvio dello scraping on the fly di LinkedIn jobs...")
    
    # Costruisci dinamicamente l'URL di ricerca in base ai parametri
    time_param = TIME_FILTERS.get(time_filter, "r86400")  # Usa il filtro temporale
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR={time_param}"
    print(f"🔍 URL di ricerca: {search_url}")
    
    jobs_data = process_jobs_on_the_fly(search_url)  # Passa la search_url al metodo di scraping
    jobs_data = jobs_data[:max_results]
    return jobs_data

if __name__ == "__main__":
    setup_signal_handling()
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="./playwright_data",
        headless=False
    )
    
    try:
        results = scrape_linkedin_jobs(query="Junior Java Developer", location="Italy", time_filter="24h")
        
        if results:
            print("\n🔽 RISULTATI FINALI JSON:")
            print(f"Trovati {len(results)} annunci di lavoro con contenuto")
            
            with open('job_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print("💾 Risultati salvati in job_results.json")
            
            print("\n📤 Invio dati all'analisi AI...")
            send_jobs_to_analysis(results)
        else:
            print("❌ Nessun risultato da inviare all'analisi.")
    
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
    
    finally:
        keep_running()
