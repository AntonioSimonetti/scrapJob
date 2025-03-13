from playwright.sync_api import sync_playwright
import time

from config.credentials import EMAIL, PASSWORD, TIME_FILTERS
from utils.file_handler import load_container_class, save_container_class
from utils.browser_utils import verify_container_class, check_login, perform_login
from utils.signal_handler import setup_signal_handling, keep_running
from scraping.scroll_handler import scroll_page
from dynamicClassFinder import find_scrollable_container

def scrape_linkedin_jobs(query="Junior Developer", location="Italy", max_results=100, time_filter="24h"):
    print("🚀 Avvio dello scraping di LinkedIn...")
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir="./playwright_data",
            headless=False
        )
        
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        page.goto("https://www.linkedin.com")
        time.sleep(3)
        
        if not check_login(page):
            perform_login(page, EMAIL, PASSWORD)
            time.sleep(5)
            print("📩 Se LinkedIn richiede un codice, inseriscilo manualmente nel browser.")
            input("⏳ Premi INVIO dopo aver completato la verifica manualmente...")

        time_param = TIME_FILTERS.get(time_filter, "r86400")
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR={time_param}"

        try:
            page.goto(search_url)
            time.sleep(5)

            container_class = load_container_class()
            
            if not verify_container_class(page, container_class):
                print("⚠️ Saved container class not working, finding new one...")
                container_class = find_scrollable_container(page)
                if container_class:
                    save_container_class(container_class)
                else:
                    print("❌ No scrollable container found")
                    return []
            
            print(f"\n🎯 Using container class: .{container_class}")
            
            all_links = []
            page_num = 1
            
            while True:
                print(f"\n📄 Scansione pagina {page_num}...")
                
                page_links = scroll_page(page, container_class)
                all_links.extend(page_links)
                
                if len(page_links) > 0:
                    print(f"✅ Trovati {len(page_links)} annunci nella pagina {page_num}")
                    
                    next_button = page.query_selector('button[aria-label="Avanti"]')
                    if next_button and not "disabled" in next_button.get_attribute("class", ""):
                        next_button.click()
                        time.sleep(3)
                        page_num += 1
                    else:
                        print("\n🏁 Raggiunta l'ultima pagina!")
                        break
                else:
                    print("\n⚠️ Nessun link trovato in questa pagina")
                    break
                
                if len(all_links) >= max_results:
                    print(f"\n🎯 Raggiunto il numero massimo di risultati ({max_results})")
                    break

            unique_links = list(set(all_links))[:max_results]
            print(f"\n🎯 Totale annunci unici trovati: {len(unique_links)}")
            
            for link in unique_links:
                print(f"🔗 {link}")
                
            return unique_links

        except Exception as e:
            print(f"Errore durante lo scraping: {e}")
            return []

if __name__ == "__main__":
    setup_signal_handling()
    results = scrape_linkedin_jobs(query="Developer", location="Italy", time_filter="24h")
    print("\n🔽 RISULTATI FINALI:")
    print(f"Trovati {len(results)} link unici")
    keep_running()