# Operacao e debug

## Fluxo oficial
- Login PHP gera token em `usuario.token`.
- `web/api/session.php` sempre devolve o token atual do banco e responde sem cache.
- Lobby abre WebSocket em `WS_URL`.
- Cliente envia `auth` e depois `room_list`, `room_create` ou `room_join`.
- Navegacao para `page=game` ocorre apenas em `match_start`.

## Portas atuais
- PHP local: `http://localhost/index.php?page=login`
- WebSocket local: `ws://127.0.0.1:8766/ws`

## Checklist rapido
- Backend responde `GET /health`.
- `web/api/session.php` retorna `ok=true` e token valido.
- 2 contas diferentes autenticam no lobby.
- Jogador A cria sala.
- Jogador B atualiza lista e entra.
- Ambos recebem `match_start`.

## Logs uteis do WS
- `[ws auth]`: autenticacao WS.
- `[room_create]`: sala criada.
- `[room_join]`: entrada em sala.
- `[match_start]`: partida iniciada.

## Falhas ja encontradas
- `UNAUTHORIZED: token invalido`
- Causas:
  - token antigo em cache do navegador
  - `session.php` devolvendo token stale da sessao
  - backend WS iniciado fora da pasta do projeto e lendo `.env` errado
  - pool MySQL do WS sem `autocommit`, lendo snapshot antigo do token
- Acao:
  - `session.php` sem cache e buscando token fresco no banco
  - `server/config.py` carregando `.env` por caminho absoluto
  - `server/db.py` com `autocommit=True`
  - reiniciar `uvicorn` apos alterar auth/config

- Partida nao retoma apos reconnect
- Causa: reentrada em sala/partida sem reenviar `match_start` e `input_seq` stale no servidor.
- Acao:
  - resetar `input_seq` ao reconectar
  - reenviar `match_start` quando o usuario volta para sala em `playing`
  - rejoin automatico no lobby somente quando existir `dk_room_id` e `dk_match_id`

- Partida pausa e encerra por desconexao
- Regra:
  - qualquer jogador desconectado em `playing` pausa a partida por 10s
  - se reconectar antes, a partida continua
  - se nao reconectar, encerra por `disconnect`

- `INVALID_STATE: falha ao entrar`
- Causa: jogador ja pertencia a sala em `playing`.
- Acao: validar pertencimento antes do bloqueio por status.

- `Table 'dekership.game_room' doesn't exist`
- Causa: schema 1v1 nao aplicado no banco alvo.
- Acao: criar `game_room`, `game_match`, `player_stats`.

- `Waiting for table metadata lock`
- Causa: sessoes antigas presas no MySQL.
- Acao: encerrar sessoes travadas e reaplicar DDL.

## Reset local recomendado
- Reiniciar `uvicorn`.
- Recarregar navegadores com `Ctrl+F5`.
- Limpar `localStorage` (`dk_room_id`, `dk_match_id`) se houver estado residual.
- Testar 2 contas em navegadores/perfis diferentes.
