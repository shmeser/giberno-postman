from re import sub

from django.contrib.gis.geoip2 import GeoIP2
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from geoip2.errors import AddressNotFoundError

from app_users.models import JwtToken, UserProfile
from backend.utils import get_request_headers


class UpdateUserLastLoginDT(MiddlewareMixin):
    def process_request(self, request):
        header_token = request.META.get('HTTP_AUTHORIZATION', None)
        if header_token is not None:
            try:
                jwt = sub('JWT ', '', request.META.get('HTTP_AUTHORIZATION', None))
                token = sub('Bearer ', '', jwt)
                token_obj = JwtToken.objects.get(access_token=token)
                token_obj.user.last_login = now()
                token_obj.user.save()
            except JwtToken.DoesNotExist:
                pass
            except UserProfile.DoesNotExist:
                pass


class UpdateRequestGeoByIP(MiddlewareMixin):
    def process_request(self, request):
        headers = get_request_headers(request)
        remote_ip = headers.get('X-Real-Ip', None)
        if remote_ip:
            try:
                g = GeoIP2()
                country = g.country(remote_ip)
                city = g.city(remote_ip)
                point = g.geos(remote_ip)
                request.geo = {
                    "country": country['country_name'],
                    "city": city['city'],
                    "point": point,
                    "ip": remote_ip
                }
            except AddressNotFoundError:
                print(f'   Адрес не найден для IP {remote_ip}')
            except Exception as e:
                print(e)
