def verify_container_class(page, container_class):
    if not container_class:
        return False
    try:
        result = page.evaluate(f"""
            () => {{
                const container = document.querySelector('.{container_class}');
                return container && container.scrollHeight > container.clientHeight;
            }}
        """)
        return result
    except:
        return False

def check_login(page):
    if page.locator('.global-nav__me').is_visible():
        print("✅ Già loggato su LinkedIn!")
        return True
    return False

def perform_login(page, email, password):
    print("🔐 Effettuando il login su LinkedIn...")
    page.goto("https://www.linkedin.com/login")
    page.fill("#username", email)
    page.fill("#password", password)
    page.click("button[type=submit]")