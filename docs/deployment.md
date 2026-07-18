# Deployment - Comcio, asystent e-commerce

## Wdrożenie natywne (systemd) - zalecane na Raspberry Pi

### Krok 1: Instalacja zależności

```bash
cd ~/allegro-assistant
git pull
uv sync
uv run alembic upgrade head
```

### Krok 2: Test ręczny

```bash
uv run python -m app.main
```

Sprawdź w innym terminalu: `curl http://127.0.0.1:8000/health`
oraz `/start` w Telegramie do bota Comcio.

### Krok 3: Instalacja usługi systemd

```bash
sudo cp scripts/comcio-assistant.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable comcio-assistant
sudo systemctl start comcio-assistant
```

**Zamień w pliku `.service`** użytkownika `pi` oraz ścieżkę
`/home/pi/allegro-assistant` na rzeczywiste wartości ze swojego
systemu (`whoami`, `pwd`).

### Krok 4: Weryfikacja

```bash
sudo systemctl status comcio-assistant
journalctl -u comcio-assistant -f
```

### Krok 5: Test restartu

```bash
sudo systemctl restart comcio-assistant
sudo reboot
```

Po restarcie: `sudo systemctl status comcio-assistant` powinno
pokazywać `active (running)` bez ręcznej interwencji.

## Wdrożenie przez Docker (alternatywa)

```bash
cd docker
docker compose up -d --build
docker compose logs -f
```

**Uwaga:** nie uruchamiaj równolegle systemd i Dockera - obie ścieżki
próbowałyby jednocześnie odpytywać Allegro API i wysyłać powiadomienia
Telegram, co prowadziłoby do zdublowanych wiadomości.
