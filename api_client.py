import requests
import json

def send_jobs_to_analysis(jobs_data):
    dotnet_api_url = "https://localhost:7169/GeminiAI/analyze-jobs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(dotnet_api_url, json=jobs_data, headers=headers, verify=False)
        
        if response.status_code == 200:
            print("\n=== 🤖 AI Analysis Results ===")
            with open("analysis_results.txt", "w") as file:
                file.write(response.text)
            #print(response.text)
            print("✅ Results saved to 'analysis_results.txt'")
            print("============================\n")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")


        