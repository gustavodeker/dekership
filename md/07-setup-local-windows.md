# Setup local Windows 11 (rede local)

## Pre-requisitos
- PHP 8.2+
- Python 3.11+
- Node.js 20+ (para Tailwind build)
- Acesso ao MariaDB na VPS (host, porta, usuario, senha, banco)

## Variaveis recomendadas
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`
- `WS_URL` (ex.: `ws://192.168.0.10:8765/ws`)

## Execucao local
1. Subir PHP:
```bash
php -S 0.0.0.0:8080
```
2. Subir servidor Python:
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8765
```
3. Compilar Tailwind (watch):
```bash
npx tailwindcss -i ./web/assets/tailwind.input.css -o ./web/assets/tailwind.css --watch
```

## Teste em rede local
- Acessar `http://<ip-local>:8080` em outro dispositivo.
- Validar conectividade WS em `ws://<ip-local>:8765/ws`.
- Garantir liberacao de portas 8080 e 8765 no firewall local.

## Seguranca minima no local
- Nao manter credenciais de VPS hardcoded em codigo.
- Usar `.env` local e carregar no PHP/Python.
- Limitar CORS/origem WS para IPs da rede local.
