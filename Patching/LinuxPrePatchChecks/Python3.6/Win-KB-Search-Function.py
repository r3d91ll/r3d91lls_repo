import requests

def get_windows_update_details(kb_number):
    url = f"https://support.microsoft.com/en-us/topic/{kb_number.lower()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return str(e)

kb_details = get_windows_update_details("KB5032310")
kb_details