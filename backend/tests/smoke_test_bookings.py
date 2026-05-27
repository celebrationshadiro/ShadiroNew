import os
import requests

BASE = os.environ.get('APP_URL', 'http://localhost:8000')

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@shadiro.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')


def login(email, password):
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()['access_token']


def smoke_test():
    print('Logging in')
    token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    headers = {'Authorization': f'Bearer {token}'}

    print('Listing vendors (admin)')
    r = requests.get(f"{BASE}/api/admin/vendors", headers=headers)
    print('vendors status:', r.status_code)
    print(r.json()[:2])

    print('Listing bookings (admin)')
    r = requests.get(f"{BASE}/api/bookings", headers=headers)
    print('bookings status:', r.status_code)
    print(r.json()[:2])


if __name__ == '__main__':
    smoke_test()
