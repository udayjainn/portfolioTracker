import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_holding_change_notification(
    fcm_tokens: list[str],
    investor_name: str,
    security_ticker: str,
    change_type: str,
    shares_change_pct: Optional[float] = None,
):
    if not fcm_tokens:
        return

    if change_type == "NEW":
        title = f"{investor_name} opened a new position"
        body = f"New holding: {security_ticker}"
    elif change_type == "SOLD":
        title = f"{investor_name} exited {security_ticker}"
        body = f"Completely sold out of {security_ticker}"
    elif change_type == "INCREASED":
        title = f"{investor_name} added to {security_ticker}"
        body = f"Increased position by {shares_change_pct:.1f}%" if shares_change_pct else "Increased position"
    elif change_type == "DECREASED":
        title = f"{investor_name} trimmed {security_ticker}"
        body = f"Reduced position by {abs(shares_change_pct):.1f}%" if shares_change_pct else "Reduced position"
    else:
        return

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            tokens=fcm_tokens,
            notification=messaging.Notification(title=title, body=body),
            data={
                "type": "HOLDING_CHANGE",
                "ticker": security_ticker,
                "change_type": change_type,
            },
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=1, sound="default")
                )
            ),
        )
        response = messaging.send_each_for_multicast(message)
        logger.info(f"FCM sent: {response.success_count} success, {response.failure_count} failed")
    except Exception as e:
        logger.error(f"FCM send failed: {e}")
