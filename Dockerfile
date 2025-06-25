# --- FASE 1: Base e Dipendenze ---
# Spiegazione: Partiamo da un'immagine Python ufficiale, leggera e ottimizzata.
FROM python:3.10-slim

# Spiegazione: Impostiamo una directory di lavoro all'interno del container.
# Tutti i comandi successivi verranno eseguiti da qui.
WORKDIR /app

# Spiegazione: Copiamo SOLO il file dei requisiti per primo.
# Docker memorizza in cache questo strato. Se i requisiti non cambiano,
# non verranno reinstallati ad ogni build, rendendo il processo molto più veloce.
COPY requirements.txt .

# Spiegazione: Installiamo le dipendenze Python.
# --no-cache-dir riduce la dimensione finale dell'immagine.
RUN pip install --no-cache-dir -r requirements.txt

# --- FASE 2: Copia dell'Applicazione ---
# Spiegazione: Ora copiamo tutto il resto del codice del nostro progetto
# nella directory /app del container.
COPY . .

# --- FASE 3: Configurazione e Avvio ---
# Spiegazione: Esponiamo la porta 5000. Gunicorn ascolterà su questa porta
# all'interno del container.
EXPOSE 5000

# Spiegazione: Questo è il comando che avvia la nostra applicazione in produzione.
# Usiamo Gunicorn invece del server di sviluppo di Flask.
# -w 4: Avvia 4 "workers" (processi) per gestire le richieste in parallelo.
# -b 0.0.0.0:5000: Dice a Gunicorn di ascoltare su tutte le interfacce di rete
# sulla porta 5000 (fondamentale per Docker).
# app:app: Indica di eseguire l'oggetto 'app' dal file 'app.py'.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
