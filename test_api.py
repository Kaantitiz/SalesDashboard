import requests
import json

# Test API endpoint
url = "http://localhost:5000/api/sales/representatives"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"Response Text: {response.text}")
        
except Exception as e:
    print(f"Error: {e}") 