import json

def load_container_class():
    try:
        with open("container_class.txt", "r") as f:
            cls = f.read().strip()
            if cls:
                print(f"📝 Loaded container class from file: {cls}")
                return cls
    except FileNotFoundError:
        print("📝 No saved container class found")
    return None

def save_container_class(cls):
    with open("container_class.txt", "w") as f:
        f.write(cls)
    print(f"💾 Saved container class to file: {cls}")

def save_fetched_links(links):
    with open('fetched_links.json', 'w') as f:
        json.dump(links, f, indent=2)
    print("💾 Links saved to fetched_links.json")

def load_fetched_links():
    try:
        with open('fetched_links.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("📝 No saved links found")
        return []