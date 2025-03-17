import json
import os

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
    if not os.path.exists('fetched_links.json'):
        with open('fetched_links.json', 'w') as f:
            json.dump([], f) 
        print("📝 Created new fetched_links.json")
        return []
    
    with open('fetched_links.json', 'r') as f:
        return json.load(f)

def save_sent_links(links):
    with open('sent_links.json', 'w') as f:
        json.dump(links, f, indent=2)
    print("💾 Links saved to sent_links.json")

def load_sent_links():
    if not os.path.exists('sent_links.json'):
        with open('sent_links.json', 'w') as f:
            json.dump([], f) 
        print("📝 Created new sent_links.json")
        return []
    
    with open('sent_links.json', 'r') as f:
        return json.load(f)
