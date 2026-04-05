# Operacao e debug

## Fluxo oficial
- Login PHP gera token em `usuario.token`.
- Lobby abre WebSocket em `WS_URL`.
- Cliente envia `auth` e depois `room_list`, `room_create` ou `room_join`.
- Navegacao para `page=game` ocorre apenas em `match_start`.

## Portas atuais
- PHP local: `http://localhost/index.php?page=login`
- WebSocket local: `ws://192.168.1.9:8766/ws`

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
- Causa: token antigo/cache de pagina.
- Acao: obter token atual via `web/api/session.php`.

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
