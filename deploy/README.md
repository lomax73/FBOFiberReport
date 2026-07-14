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
