class JwtTokenEntity:
    def __init__(
            self,
            user=None,
            access_token=None,
            refresh_token=None,
            app_version=None,
            platform_name=None,
            vendor=None
    ) -> None:
        self.user = user
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.app_version = app_version
        self.platform_name = platform_name
        self.vendor = vendor

    def get_kwargs(self):
        return {
            'user': self.user,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'app_version': self.app_version,
            'platform_name': self.platform_name,
            'vendor': self.vendor
        }


class SocialEntity:
    def __init__(
            self,
            first_name=None,
            last_name=None,
            middle_name=None,
            username=None,
            social_id=None,
            social_type=None,
            access_token=None,
            access_token_expiration=None,
            phone=None,
            email=None
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.username = username
        self.phone = phone
        self.email = email
        self.social_id = social_id
        self.social_type = social_type
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration

    def get_kwargs(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'social_id': self.social_id,
            'type': self.social_type,
            'access_token': self.access_token,
            'access_token_expiration': self.access_token_expiration
        }


class SettingsEntity:
    def __init__(self, user) -> None:
        self.user = user

    def get_kwargs(self):
        return {
            'user': self.user,
        }


class TokenEntity:
    def __init__(self, token):
        self.token = token
