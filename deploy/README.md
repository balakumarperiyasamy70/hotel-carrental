# Sands Car Rental — Server Setup & Deployment

## Server
- **Host:** Bluehost VPS
- **IP:** 129.121.85.32
- **OS:** Ubuntu 24.04
- **App directory:** /opt/hotel-carrental
- **Port:** 8005 (Gunicorn)

## Stack
- Python 3.12 + Flask
- Gunicorn (WSGI server)
- Nginx (reverse proxy + SSL)
- MariaDB (database)
- Let's Encrypt (SSL)
- ReportLab (PDF generation)

---

## Initial Deployment Steps

### 1. DNS record (at Bluehost)
Add A record: `carrental` → `129.121.85.32`

### 2. Clone repo
```bash
cd /opt
git clone https://github.com/balakumarperiyasamy70/hotel-carrental.git
cd hotel-carrental
```

### 3. Python virtual environment
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 4. Database setup
```bash
mysql -u root -p -e "
CREATE DATABASE sandscarrental CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'carrental'@'127.0.0.1' IDENTIFIED BY 'CarRental2026!';
GRANT ALL PRIVILEGES ON sandscarrental.* TO 'carrental'@'127.0.0.1';
FLUSH PRIVILEGES;"

mysql -u root -p sandscarrental < schema.sql
```

### 5. Set admin password
```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('CarRentalAdmin2026!'))"
# Copy the hash, then:
mysql -u root -p sandscarrental -e "UPDATE admin_users SET password_hash='<paste-hash-here>' WHERE username='admin';"
```

### 6. Create .env file
```bash
cp .env.example .env
nano .env
```
Fill in:
- SECRET_KEY — `python3 -c "import secrets; print(secrets.token_hex(32))"`
- DB_PASSWORD — CarRental2026!

### 7. Set permissions
```bash
chown -R www-data:www-data /opt/hotel-carrental
```

### 8. Systemd service
```bash
cp deploy/hotel-carrental.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hotel-carrental
systemctl start hotel-carrental
systemctl status hotel-carrental
```

### 9. Nginx config
```bash
cp deploy/nginx.conf /etc/nginx/sites-available/carrental.sandshotel.us.conf
ln -s /etc/nginx/sites-available/carrental.sandshotel.us.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 10. SSL certificate
```bash
certbot --nginx -d carrental.sandshotel.us
systemctl reload nginx
```

---

## Ongoing Updates

**On Windows PC:**
```powershell
git add .
git commit -m "describe change"
git push
```

**On server:**
```bash
cd /opt/hotel-carrental
git pull
systemctl restart hotel-carrental
```

---

## Admin Panel
- URL: https://carrental.sandshotel.us/admin
- Username: admin
- Password: CarRentalAdmin2026!

## Database Credentials
- Database: sandscarrental
- User: carrental
- Password: CarRental2026!
- Host: 127.0.0.1

---

## Deployment Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-04-12 | Repo created | GitHub: balakumarperiyasamy70/hotel-carrental |
