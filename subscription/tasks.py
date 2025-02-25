# # In tasks.py
# from celery import shared_task

# @shared_task
# def check_subscription_status():
#     # Check expiring subscriptions and update status
#     expired_subs = UserSubscription.objects.filter(
#         end_date__lt=timezone.now(),
#         is_active=True
#     )
    
#     for sub in expired_subs:
#         if sub.purchase_method in ['PLAY_STORE', 'APP_STORE']:
#             # Re-validate with platform
#             is_valid, _ = validate_platform_purchase(sub.receipt_data, sub.purchase_method)
#             sub.is_active = is_valid
#             sub.save()