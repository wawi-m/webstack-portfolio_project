import requests
import sys
import time

def test_server():
    url = "http://localhost:5000/api/v1/"
    max_retries = 5
    retry_delay = 2  # seconds
    
    print("Testing Flask server connection...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("\n[SUCCESS] Server is running successfully!")
                print("\nServer Details:")
                print(f"- URL: {url}")
                print(f"- Status: {response.status_code} OK")
                print(f"- Response: {response.json()}")
                return True
        except requests.ConnectionError:
            if attempt < max_retries - 1:
                print(f"Attempting to connect... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("\n[ERROR] Could not connect to the server!")
                print("\nPossible issues:")
                print("1. Make sure the Flask application is running (python run.py)")
                print("2. Check if port 5000 is available")
                print("3. Verify there are no firewall restrictions")
                return False

if __name__ == "__main__":
    success = test_server()
    if not success:
        sys.exit(1)
