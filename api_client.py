import requests
import time
import json
import os

def send_jobs_to_analysis(jobs_data, query, location, time_filter):
    dotnet_api_url = "https://localhost:7169/GeminiAI/analyze-jobs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Creazione della cartella se non esiste
    results_dir = "analysis_results"
    os.makedirs(results_dir, exist_ok=True)

    try:
        response = requests.post(dotnet_api_url, json=jobs_data, headers=headers, verify=False)
        
        if response.status_code == 200:
            print("\n=== 🤖 AI Analysis Results ===")

            # Crea un nome file basato su query, location e filtro tempo
            safe_query_name = query.replace(" ", "_")  
            safe_location_name = location.replace(" ", "_")  
            file_name = f"{safe_query_name}_{safe_location_name}_{time_filter}.txt"
            file_path = os.path.join(results_dir, file_name)

            # Salva i risultati nel file (sovrascrivendo se esiste)
            with open(file_path, "w") as file:
                file.write(response.text)
            
            print(f"✅ Results saved to '{file_path}'")
            print("============================\n")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")
