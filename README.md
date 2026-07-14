# Collaudi Fibra

App della famiglia FBO per il collaudo di tratte in fibra ottica: crea un
progetto/cantiere, registra le tratte cablate con le misure rilevate in
campo (per lunghezza d'onda e direzione), verifica se il valore misurato è
plausibile rispetto a quello teorico atteso (fibra + giunzioni +
connettori), e genera un report PDF per il cliente.

Basata sul calcolo dell'utility HTML originale
`FIber_util&report/calcolo_attenuazione_fibra.html` (stessi coefficienti,
portati in `collaudi/services.py`).

## Sviluppo locale

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py runserver
```

WeasyPrint richiede Pango installato a livello di sistema:
`brew install pango` su macOS, vedi `deploy/README.md` per Linux/produzione.

## Flusso

1. Crea un progetto (cantiere, indirizzo, logo, tolleranza di plausibilità).
2. Aggiungi una tratta (partenza/arrivo, fibra, lunghezza, giunzioni,
   connettori, data/ora test) — vengono create automaticamente le righe di
   misura per ogni combinazione lunghezza d'onda × direzione pertinente.
3. Inserisci i valori misurati nella pagina "Misure".
4. Dalla scheda progetto, "Genera report PDF".

## Deploy

Vedi `deploy/README.md`.
