# Setup Windows 11 + Debian 12 (VPS)

## Pre-requisitos
- Laragon 7 (PHP 8.2+)
- Python 3.11+
- Acesso ao MariaDB na VPS (host, porta, usuario, senha, banco)

## Variaveis recomendadas
- `DB_HOST=191.252.38.111`
- `DB_PORT=3333`
- `DB_NAME=dekership`
- `DB_USER=externo`
- `DB_PASS=Sistema@123`
- `WS_URL=ws://192.168.1.9:8766/ws`

## Execucao local (venv em diante)
1. Entrar na raiz do projeto:
```powershell
cd "G:\My Drive\01 - Projetos\Andamento\Dekership"
```
2. Criar venv:
```powershell
py -3.11 -m venv .venv
```
3. Ativar venv:
```powershell
.\.venv\Scripts\Activate.ps1
```
4. Atualizar pip:
```powershell
python -m pip install --upgrade pip
```
5. Instalar dependencias Python:
```powershell
pip install -r requirements.txt
```
6. Subir backend Python:
```powershell
uvicorn server.app:app --host 0.0.0.0 --port 8766
```
7. Subir PHP no Laragon 7:
- Abrir Laragon.
- Definir pasta do projeto como root do site local.
- Iniciar servicos e acessar via URL local do Laragon.
8. CSS Tailwind:
- Usar `./web/assets/tailwind.css` ja compilado no repositorio.

## requirements.txt
- Manter arquivo `requirements.txt` na raiz do projeto.
- Sempre instalar com `pip install -r requirements.txt` apos ativar o venv.

## Teste em rede local
- Acessar `http://<ip-local>:8080` em outro dispositivo.
- Validar conectividade WS em `ws://<ip-local>:8766/ws`.
- Garantir liberacao de portas 8080 e 8766 no firewall local.

## Seguranca minima no local
- Nao manter credenciais de VPS hardcoded em codigo.
- Usar `.env` local e carregar no PHP/Python.
- Limitar CORS/origem WS para IPs da rede local.

---

## Setup Debian 12 (VPS)

### Pre-requisitos
- `nginx` configurado no dominio/subdominio
- `python3`, `python3-venv`, `python3-pip`, `git`
- acesso ao mesmo MariaDB (host, porta, usuario, senha, banco)

### Variaveis recomendadas (mesmo banco)
- `DB_HOST=191.252.38.111`
- `DB_PORT=3333`
- `DB_NAME=dekership`
- `DB_USER=externo`
- `DB_PASS=Sistema@123`
- `WS_URL=wss://<seu-dominio>/ws`

### Execucao na VPS (venv em diante)
1. Entrar no projeto:
```bash
cd /var/www/dekership
```
2. Instalar pacotes base:
```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
```
3. Criar venv:
```bash
python3 -m venv .venv
```
4. Ativar venv:
```bash
source .venv/bin/activate
```
5. Atualizar pip e instalar dependencias:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
6. Testar backend manualmente:
```bash
uvicorn server.app:app --host 127.0.0.1 --port 8766
```

### Servico systemd (WebSocket)
1. Criar arquivo:
```bash
sudo nano /etc/systemd/system/dekership-ws.service
```
2. Conteudo:
```ini
[Unit]
Description=Dekership WebSocket (Uvicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/dekership
EnvironmentFile=/var/www/dekership/.env
ExecStart=/var/www/dekership/.venv/bin/uvicorn server.app:app --host 127.0.0.1 --port 8766
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
3. Habilitar e iniciar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dekership-ws
sudo systemctl status dekership-ws
```

### Nginx reverse proxy (WS)
- apontar `/ws` para `http://127.0.0.1:8766/ws`
- manter cabecalhos:
  - `Upgrade $http_upgrade`
  - `Connection "upgrade"`
  - `Host $host`

### Operacao
- deploy/update: `git pull`, ativar venv, `pip install -r requirements.txt`, `sudo systemctl restart dekership-ws`
- logs: `journalctl -u dekership-ws -f`
