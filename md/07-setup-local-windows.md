# Setup local Windows 11 (rede local)

## Pre-requisitos
- Laragon 7 (PHP 8.2+)
- Python 3.11+
- Acesso ao MariaDB na VPS (host, porta, usuario, senha, banco)

## Variaveis recomendadas
- `DB_HOST=191.252.38.111`
- `DB_PORT=3333`
- `DB_NAME=dekership`
- `DB_USER=externo`
- `DB_PASS=<definir_no_env_local>`
- `WS_URL` (ex.: `ws://192.168.1.9:8766/ws`)

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
