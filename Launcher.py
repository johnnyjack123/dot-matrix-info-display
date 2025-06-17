import requests

def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

# Beispiel:
if check_internet_connection():
    print("Internet connection")

else:
    print("No internet connection")
