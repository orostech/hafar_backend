# Update payment handler with async task
# wallet/tasks.py
from celery import shared_task
from .payment_handlers import FlutterwaveHandler

@shared_task
def verify_payment_task(tx_ref):
    handler = FlutterwaveHandler()
    return handler.verify_payment(tx_ref)