import json
import firebase_admin
from firebase_admin import credentials, messaging
from settings.credential_settings import credential_setting
# Global variable to hold the Firebase app instance
firebase_app = None


def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using service account credentials.

    This function ensures the Firebase app is initialized only once during the application's lifecycle.
    It retrieves the service account credentials from the environment configuration and creates a
    global Firebase app instance. This setup is required before sending any Firebase Cloud Messaging (FCM)
    notifications.

    Raises:
        ValueError: If the credentials are missing or improperly formatted.
        firebase_admin.exceptions.FirebaseError: If Firebase initialization fails.
    """
    
    global firebase_app
    if not firebase_admin._apps:  
        json_data = credential_setting.firebase_development  
        firebase_config = json.loads(json_data) 
        cred = credentials.Certificate(firebase_config) 
        firebase_app = firebase_admin.initialize_app(cred)
        
        
        
        
def send_fcm_notification(token, title: str, body: str, data: dict = None , image:str = None):
    """
    Sends a push notification to a specific device using Firebase Cloud Messaging (FCM).

    Args:
        token (str): The FCM registration token of the target device.
        title (str): The title of the notification.
        body (str): The body text of the notification.
        data (dict, optional): A dictionary of custom key-value pairs to include in the message payload.

    Returns:
        dict: A dictionary indicating the success status and either the message ID or error details.
              Example on success: {"success": True, "message_id": "<message-id>"}
              Example on failure: {"success": False, "error": "<error-message>"}

    Raises:
        firebase_admin.exceptions.FirebaseError: If sending the message fails due to a Firebase-related issue.
    """
    if isinstance(token, dict):
        for k , v in token.items():
            send_fcm_notification(v , title , body , data , image)
            
    elif isinstance(token , str):
        message = None
        if image:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body , image=image),
                data=data if data else {},
                token=token
            )
        else:
             message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data if data else {},
                token=token
            )
        try:
            response = messaging.send(message)
            return {"success": True, "message_id": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

