class JwtTokenEntity:
    def __init__(self, user, access_token, refresh_token, app_version, platform_name, vendor) -> None:
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
    def __init__(self, user, social_type, access_token, access_token_expiration, phone, email) -> None:
        self.user = user
        self.phone = phone
        self.email = email
        self.social_id = user.uid
        self.social_type = social_type
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration

    def get_kwargs(self):
        return {
            'user': self.user,
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
