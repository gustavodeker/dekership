# Dekership 1v1

## Stack
- PHP (login/cadastro/sessao/lobby/game/perfil/ranking)
- Python FastAPI + WebSocket (servidor autoritativo 1v1)
- MariaDB (usuario, game_room, game_match, player_stats)

## Sequencia de execucao
1. Criar `.env` na raiz com base em `.env.example`.
2. Aplicar migration `BANCO/migrations/001_1v1_schema.sql` no MariaDB.
3. Criar/ativar venv e instalar dependencias:
   - `py -3.11 -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
   - `pip install -r requirements.txt`
4. Subir backend WS:
   - `uvicorn server.app:app --host 0.0.0.0 --port 8765`
5. Subir PHP local (Laragon/Nginx) e abrir `index.php?page=login`.
6. Login com 2 clientes, criar/entrar em sala e validar fim no 3o hit.

## Endpoints backend
- `GET /health`
- `GET /rooms`
- `GET /ranking`
- `GET /profile?token=<TOKEN_SESSAO_PHP>`
- `WS /ws`

## Fluxo funcional
- Login PHP gera token de sessao em `usuario.token`.
- Cliente WS autentica com evento `auth`.
- Lobby cria/lista/entra em sala (`room_create`, `room_list`, `room_join`).
- Com 2 jogadores, partida inicia automaticamente.
- Cliente envia apenas `player_input` (movimento/tiro).
- Servidor calcula estado/hit/vitoria e persiste resultado em transacao unica.