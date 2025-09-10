import asyncio
import requests
from settings.credential_settings import credential_setting


ACCESS_TOKEN = ""
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

async def send_whatsapp_message(phone_number: str, message: str):
    
    """
    Send a WhatsApp message to a specified phone number using the WhatsApp Business Cloud API.

    This function constructs and sends a POST request to the Meta Graph API's 
    `/messages` endpoint for WhatsApp using the provided phone number and message text.

    Args:
        phone_number (str): The recipient's phone number in international format (e.g., "+917303444340").
        message (str): The message content to be sent via WhatsApp.

    Returns:
        dict: A dictionary containing the status of the message delivery. If successful, 
        returns {"status": "Message sent successfully"}. On failure, includes the error response 
        from the WhatsApp API.

    Notes:
        - Ensure that `ACCESS_TOKEN` and `PHONE_NUMBER_ID` are correctly configured and valid.
        - This function uses synchronous HTTP requests (`requests`) even though it's declared `async`.
          Consider switching to `httpx.AsyncClient` for full async support if used in an async context.
    """
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        return {"status": "Message sent successfully"}
    else:
        return {"status": "Failed to send message", "error": response.json()}
    
    

if __name__ == "__main__":
    asyncio.run(send_whatsapp_message("+91 7303444340" , "testing message"))