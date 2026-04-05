# Protocolo WebSocket (cliente <-> servidor)

## Envelope padrao
```json
{
  "event": "nome_evento",
  "request_id": "uuid-opcional",
  "payload": {}
}
```

## Eventos cliente -> servidor
- `auth`
  - payload: `{ "token": "TOKEN_SESSAO_PHP" }`
- `room_create`
  - payload: `{ "room_name": "Sala 1" }`
- `room_list`
  - payload: `{}`
- `room_join`
  - payload: `{ "room_id": "uuid" }`
- `player_input`
  - payload: `{ "seq": 12, "move_x": -1|0|1, "shoot": true|false }`
- `ping`
  - payload: `{ "ts": 1712345678 }`

## Eventos servidor -> cliente
- `auth_ok`
  - payload: `{ "user_id": 10, "username": "ana" }`
- `room_created`
  - payload: `{ "room_id": "uuid", "status": "waiting" }`
- `room_list_result`
  - payload: `{ "rooms": [{ "room_id": "uuid", "name": "Sala 1", "players": 1 }] }`
- `room_joined`
  - payload: `{ "room_id": "uuid", "side": "bottom|top", "players": 2 }`
- `match_start`
  - payload: `{ "match_id": "uuid", "tick_rate": 30 }`
- `state`
  - payload: `{ "tick": 145, "p1": {...}, "p2": {...}, "projectiles": [...], "score": { "p1": 2, "p2": 1 } }`
- `hit`
  - payload: `{ "match_id": "uuid", "attacker": 10, "target": 11, "score": { "attacker": 3, "target": 1 } }`
- `match_end`
  - payload: `{ "match_id": "uuid", "winner_user_id": 10, "reason": "3_hits|disconnect" }`
- `pong`
  - payload: `{ "ts": 1712345678 }`
- `error`
  - payload: `{ "code": "ROOM_FULL|UNAUTHORIZED|INVALID_STATE|RATE_LIMIT", "message": "..." }`

## Regras de sincronizacao
- Cliente envia apenas input, nunca estado final.
- Servidor usa `seq` para descartar input antigo.
- `state` enviado em intervalo fixo (ex.: 20-30 Hz).
- Heartbeat: `ping/pong` a cada 5s; queda apos 2 perdas consecutivas.
