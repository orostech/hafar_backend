# notifications/email_service.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from postmarker.core import PostmarkClient
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.client = PostmarkClient(server_token=settings.POSTMARK_API_KEY)
        self.default_from_email = settings.DEFAULT_FROM_EMAIL
        self.site_name = "Hafar"  # Replace with your app name

    def _send_email_template(self, to_email, subject, template_name, context):
        """
        Helper method to send templated emails
        """
        if settings.DEBUG:
            return print('Debug mode')
        try:
            # Render HTML and text versions
            html_content = render_to_string(
                f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)

            # Send via Postmark
            self.client.emails.send(
                From=self.default_from_email,
                To=to_email,
                Subject=subject,
                HtmlBody=html_content,
                TextBody=text_content,
                MessageStream='outbound'  # or 'broadcast' for bulk emails
            )
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_welcome_email(self, user):
        """Send welcome email after registration"""
        context = {
            'user': user,
            'site_name': self.site_name,
            'login_url': f"{settings.FRONTEND_URL}/login"
        }
        return self._send_email_template(
            user.email,
            f"Welcome to {self.site_name}!",
            'welcome',
            context
        )

    def send_login_alert(self, user, context):
        subject = "New Login Activity Detected"  
        return self._send_email_template(
            user.email,
            subject,
            'login_alert',
            context
        )


    def send_match_notification(self, match):
        """Send email when users match"""
        for user in [match.user1, match.user2]:
            matched_with = match.user2 if user == match.user1 else match.user1
            context = {
                'user': user,
                'matched_with': matched_with,
                'match_url': f"{settings.FRONTEND_URL}/matches/{match.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                user.email,
                "You have a new match! 🎉",
                'new_match',
                context
            )

    def send_like_notification(self, like):
        """Send email when user receives a like"""
        if like.liked.profile.email_notifications:  # Check user preferences
            context = {
                'user': like.liked,
                'liker': like.liker,
                'like_type': like.like_type,
                'profile_url': f"{settings.FRONTEND_URL}/profile/{like.liker.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                like.liked.email,
                "Someone liked your profile! ❤️",
                'new_like',
                context
            )

    def send_message_notification(self, message):
        """Send email for new messages"""
        if message.recipient.profile.new_messages_notitication:
            context = {
                'user': message.recipient,
                'sender': message.sender,
                'message_preview': message.content[:100],
                'chat_url': f"{settings.FRONTEND_URL}/messages/{message.chat.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                message.recipient.email,
                "You have a new message 💌",
                'new_message',
                context
            )

    def send_profile_view_notification(self, visit):
        """Send email when someone views a profile"""
        if visit.visited.profile.profile_view_notitication:
            context = {
                'user': visit.visited,
                'visitor': visit.visitor,
                'profile_url': f"{settings.FRONTEND_URL}/profile/{visit.visitor.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                visit.visited.email,
                "Someone viewed your profile 👀",
                'profile_view',
                context
            )

    def send_verification_email(self, user, verification_token):
        """Send email verification link"""
        context = {
            'user': user,
            'verification_url': f"{settings.FRONTEND_URL}/verify-email/{verification_token}",
            'site_name': self.site_name
        }
        return self._send_email_template(
            user.email,
            "Verify your email address",
            'verify_email',
            context
        )

    def send_weekly_matches_digest(self, user, matches):
        """Send weekly digest of new matches and activity"""
        context = {
            'user': user,
            'matches': matches,
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'site_name': self.site_name
        }
        return self._send_email_template(
            user.email,
            "Your Weekly Dating Digest ✨",
            'weekly_digest',
            context
        )

    def send_password_reset_otp(self, user, code):
        context = {
            'user': user,
            'code': code,
            'site_name': self.site_name
        }
        return self._send_email_template(
            user.email,
            "Password Reset OTP",
            'password_reset_otp',
            context
        )


    def send_chat_notification(self, user, other_user, chat):
        """Send email when a new chat is created"""
        if user.profile.new_chats_notitication:
            context = {
                'user': user,
                'other_user': other_user,
                'chat_url': f"{settings.FRONTEND_URL}/messages/{chat.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                user.email,
                f"You can now chat with {other_user.profile.display_name}! 💬",
                'new_chat',
                context
            )

    def send_request_accepted_notification(self, user, other_user, request):
        """Send email when message request is accepted"""
        if user.profile.new_messages_notitication:
            context = {
                'user': user,
                'other_user': other_user,
                'chat_url': f"{settings.FRONTEND_URL}/messages/{request.chat.id}",
                'site_name': self.site_name
            }
            self._send_email_template(
                user.email,
                f"{other_user.profile.display_name} accepted your request! ✅",
                'request_accepted',
                context
            )