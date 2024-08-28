import requests
'''Work in progress please leave this place da da dee ba da bum tsk tsk'''
def send_request(phoneNumber):
    data = {
        "phone_number": phoneNumber,
        "from": None,
        "model": "enhanced",
        "language": "en",
        "voice": "Alexa",
        "voice_settings": {},
        "pathway_id": None,
        "local_dialing": False,
        "max_duration": "24",
        "answered_by_enabled": False,
        "wait_for_greeting": True,
        "record": False,
        "amd": False,
        "interruption_threshold": 190,
        "voicemail_message": None,
        "temperature": None,
        "transfer_phone_number": None,
        "transfer_list": {},
        "metadata": {},
        "pronunciation_guide": [
            {"word": "VX", "pronunciation": "Vee-X", "case_sensitive": False, "spaced": False},
            {"word": "Ariphanil", "pronunciation": "A-Ri-Pha-Neal", "case_sensitive": False, "spaced": False}
        ],
        "start_time": None,
        "request_data": {},
        "tools": [],
        "dynamic_data": [],
        "analysis_preset": None,
        "analysis_schema": {},
        "webhook": None,
        "calendly": {}
    }

    try:
        response = requests.post('http://localhost:5000/api/make_request', json=data)
        print("Response Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
