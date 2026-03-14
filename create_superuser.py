import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemach.settings')
django.setup()

from django.contrib.auth.models import User

username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email    = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@gemach.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created!")
else:
    print(f"Superuser '{username}' already exists.")