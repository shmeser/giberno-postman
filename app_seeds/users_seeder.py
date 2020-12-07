import os
import sys

from django.utils.timezone import now

from backend.utils import timestamp_to_datetime


class AdminSeeder:

    def create(self, refresh=False):
        if refresh is True:
            self.truncate_table()

        self.create_superuser()

    # TRUNCATE TABLE
    @staticmethod
    def truncate_table():
        UserProfileModel.objects.all().delete()
        sys.stdout.write("Truncate auth_user table ... [OK]\n")

    # CREATE SUPERUSER
    @staticmethod
    def create_superuser():
        if UserProfileModel.objects.filter(username='admin').count():
            sys.stdout.write('User admin already exists!\n')
            return False
        else:
            u = UserProfileModel(
                is_superuser=True,
                username='admin',
                first_name='firstName',
                last_name='lastName',
                name='firstName lastName',
                email='superadmin@admin.com',
                is_staff=True,
                is_active=True,
                birth_date=timestamp_to_datetime(0),
                date_joined=now()
            )
            u.set_password(os.getenv('SUPERUSER_PASS', 'admin'))
            u.save()

            sys.stdout.write("Superuser created successfully!\n")
            return u.id
