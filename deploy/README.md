# Deploy sul VPS

Stesso pattern già in uso per MKRemote e il Portale (repo separato, utente
di sistema dedicato, venv proprio). Al momento nessun dominio è
configurato sul VPS: si usa l'IP nudo su una porta dedicata (vedi
`nginx-fiberreport-ip-provisional.conf`), da sostituire con un
sottodominio quando ci sarà un dominio reale.

**Dipendenza in più rispetto al Portale**: il PDF è generato con
WeasyPrint, che richiede librerie di sistema (non pacchetti Python):

```
apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2
```

## Provisioning iniziale (una tantum)

```
# da root sul VPS
adduser --system --group --home /opt/fiberreport fiberreport
mkdir -p /opt/fiberreport/app
chown fiberreport:fiberreport /opt/fiberreport/app

apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2

sudo -u fiberreport git clone <url-repo> /opt/fiberreport/app
cd /opt/fiberreport/app
sudo -u fiberreport python3 -m venv venv
sudo -u fiberreport venv/bin/pip install -r requirements.txt

cp .env.example .env   # poi valorizzare DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS
sudo -u fiberreport venv/bin/python manage.py migrate
sudo -u fiberreport venv/bin/python manage.py collectstatic --noinput
sudo -u fiberreport venv/bin/python manage.py createsuperuser
mkdir -p /opt/fiberreport/app/media && chown fiberreport:fiberreport /opt/fiberreport/app/media

cp deploy/fiberreport-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now fiberreport-web.service

cp deploy/nginx-fiberreport-ip-provisional.conf /etc/nginx/sites-available/fiberreport
ln -s /etc/nginx/sites-available/fiberreport /etc/nginx/sites-enabled/fiberreport
nginx -t && systemctl reload nginx
ufw allow <porta>/tcp comment 'Collaudi Fibra HTTPS'
```

Ricorda anche: `chmod 751 /opt/fiberreport` (come per `/opt/portal`) perché
Nginx/www-data possa attraversare la home e servire `staticfiles/` e
`media/` (i loghi caricati).

## API interna di gestione utenti (per il Portale)

Come per MKRemote, questa app espone `accounts/` sotto `api/internal/`
per permettere al Portale FBO di creare/modificare/eliminare utenti da
remoto. **Va esposta solo in locale**, mai pubblicamente:

1. Aggiungere `INTERNAL_API_TOKEN` a `.env` (vedi `.env.example`):
   ```
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Aggiungere al vhost Nginx (`nginx-fiberreport-ip-provisional.conf` o
   quello a dominio) un location block dedicato **prima** di quello
   generico `location /`, con l'accesso limitato a localhost:
   ```nginx
   location /api/internal/ {
       allow 127.0.0.1;
       deny all;
       proxy_pass http://unix:/run/fiberreport/gunicorn.sock;
       proxy_set_header Host $http_host;
   }
   ```
3. `systemctl restart fiberreport-web.service` dopo aver aggiornato `.env`.
4. Configurare lo stesso token nel Portale (admin → AppLink di Collaudi
   Fibra → campo "API token"), insieme a `internal_base_url =
   https://127.0.0.1:8444`.

## Deploy di un aggiornamento

```
ssh mkremote-vps
cd /opt/fiberreport/app
sudo -u fiberreport git pull origin main
sudo -u fiberreport venv/bin/pip install -r requirements.txt
sudo -u fiberreport venv/bin/python manage.py migrate
sudo -u fiberreport venv/bin/python manage.py collectstatic --noinput
systemctl restart fiberreport-web.service
```
