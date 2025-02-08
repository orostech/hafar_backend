from rest_framework.viewsets import ReadOnlyModelViewSet
from users.const import *
from .models import AppConfiguration
from .serializer import AppConfigurationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response



class ConfigurationViewSet(ReadOnlyModelViewSet):
    queryset = AppConfiguration.objects.filter(is_active=True)
    serializer_class = AppConfigurationSerializer

    @action(detail=False, methods=['get'])
    def initial_load(self, request):
        config_data = {
            'app_version': {
                'min_supported': '1.0.0',
                'latest': '1.0.0',
                'force_update': False
            },
            'choices': {
                # 'gender': self._format_choices(GENDER_CHOICES),
                # 'interest_in': self._format_choices(INTEREST_IN_CHOICES),
                # 'relationship': self._format_choices(RELATIONSHIP_CHOICES),
                # 'body_type': self._format_choices(BODY_TYPE_CHOICES),
                # 'complexion': self._format_choices(COMPLEXION_CHOICES),
                # 'pets': self._format_choices(DO_YOU_HAVE_PETS_CHOICES),
                # 'smoking': self._format_choices(SMOKING_CHOICES),
                # 'drinking': self._format_choices(DRINKING_CHOICES),
                # 'user_type': self._format_choices(USER_TYPE_CHOICES),
                # 'dietary': self._format_choices(DIETARY_PREFERENCES_CHOICES),
                # 'relationship_status': self._format_choices(RELATIONSHIP_STATUS_CHOICES),
                'account_status': self._format_choices(ACCOUNT_STATUS_CHOICES),
                'visibility': self._format_choices(VISIBILITY_CHOICES),
                # 'interests': self._format_choices(INTEREST_CATEGORIES),
                'verification_status': self._format_choices(VERIFICATION_STATUS_CHOICES)
            },
            'defaults': {
                'max_photos': 9,
                'max_interests': 5,
                'min_age': 18,
                'max_age': 100,
                'default_radius': 100,
            }
        }
        
        return Response(config_data)
    
    def _format_choices(self, choices):
        return [{'code': code, 'label': label} for code, label in choices]
    

       
