from sqlalchemy.orm import Session
from app.database.models import FcmToken
from firebase_admin import messaging


def send_notification_to_user(user_id: int, title: str, body: str, image: str, link : str, db: Session, chat_room_id : str):
    # user_id에 해당하는 모든 FCM 토큰을 가져옴
    tokens = db.query(FcmToken).filter(FcmToken.userId == user_id).all()

    if not tokens:
        raise ValueError("No FCM tokens found for the user")

    # 각 토큰에 대해 알림을 전송
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image
            ),
            data={
                "link": link,
                "chat_room_id": chat_room_id
            }, 
            token=token.token,
        )
        
        try:
            # Firebase로 메시지 전송
            response = messaging.send(message)
            print(f'Successfully sent message: {response}')
        except Exception as e:
            print(f'Error sending message to {token.token}: {str(e)}')
