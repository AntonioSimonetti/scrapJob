import time

def scroll_page(page, container_class):
    print("📜 Starting incremental scroll and link collection...")
    
    all_links = []
    seen_links = set()
    scroll_percentage = 0
    
    while scroll_percentage <= 100:
        page.evaluate(f"""
            () => {{
                const container = document.querySelector('.{container_class}');
                const scrollHeight = container.scrollHeight;
                container.scrollTo(0, scrollHeight * {scroll_percentage/100});
            }}
        """)
        time.sleep(2)
        
        print(f"📊 Scrolled to {scroll_percentage}%, fetching links...")
        
        elements = page.query_selector_all('.job-card-container__link')
        
        for element in elements:
            link = element.get_attribute('href')
            if link and link not in seen_links:
                full_link = f"https://www.linkedin.com{link}"
                seen_links.add(link)
                all_links.append(full_link)
                print(f"Found new job link #{len(all_links)}")
        
        scroll_percentage += 10
        
    print(f"\n✅ Total unique links found: {len(all_links)}")
    return all_links