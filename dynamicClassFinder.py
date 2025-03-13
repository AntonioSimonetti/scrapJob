import time

def find_scrollable_container(page):
    """
    Finds the scrollable container on LinkedIn jobs page dynamically.
    Returns the class name of the container that makes the footer visible when scrolled.
    """
    print("\n🔍 Ricerca del container scrollabile in corso...")
    
    candidates = page.evaluate('''() => {
        const allElements = Array.from(document.querySelectorAll("*"));
        return allElements
            .map((el, idx) => {
                const rect = el.getBoundingClientRect();
                const visible = rect.width > 0 && rect.height > 0;
                return { 
                    index: idx, 
                    tag: el.tagName, 
                    id: el.id, 
                    className: el.className, 
                    scrollHeight: el.scrollHeight, 
                    clientHeight: el.clientHeight, 
                    visible: visible 
                };
            })
            .filter(obj => obj.visible && obj.scrollHeight > obj.clientHeight);
    }''')
    
    print(f"Trovati {len(candidates)} elementi scrollabili dinamicamente.")
    
    for candidate in candidates:
        idx = candidate["index"]
        class_name = candidate["className"]
        
        if not class_name or class_name.strip() == "":
            continue
            
        print(f"\n🛠 Testing candidate index {idx}: {class_name}")
        
        try:
            # Check footer visibility before scroll
            footer_visible_before = page.evaluate('''() => {
                const footer = document.querySelector("#compactfooter-copyright");
                return footer ? footer.getBoundingClientRect().top < window.innerHeight : false;
            }''')
            
            # Perform scroll
            page.evaluate(f"""
                () => {{
                    const container = document.querySelectorAll("*")[{idx}];
                    container.scrollTo(0, container.scrollHeight);
                }}
            """)
            time.sleep(2)
            
            # Check footer visibility after scroll
            footer_visible_after = page.evaluate('''() => {
                const footer = document.querySelector("#compactfooter-copyright");
                return footer ? footer.getBoundingClientRect().top < window.innerHeight : false;
            }''')
            
            if not footer_visible_before and footer_visible_after:
                print(f"✅ Scroll riuscito! Container trovato: {class_name}")
                return class_name.split()[0]  # Return first class if multiple classes
        except Exception as e:
            print(f"Errore nel test dell'elemento index {idx}: {e}")
            continue
    
    print("\n❌ Nessun container scrollabile trovato automaticamente.")
    return None