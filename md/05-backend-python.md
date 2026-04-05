# Backend Python (FastAPI + WebSocket)

## Stack
- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy Core ou aiomysql (acesso MariaDB)
- Pydantic (validacao payload)

## Estrutura sugerida
```text
server/
  app.py
  config.py
  db.py
  auth.py
  ws/
    router.py
    events.py
    connection_manager.py
  domain/
    rooms.py
    matches.py
    simulation.py
    ranking.py
```

## Responsabilidades
- `auth.py`: validar token de sessao PHP contra tabela `usuario`.
- `rooms.py`: criar/listar/entrar sala.
- `matches.py`: iniciar partida com 2 jogadores e encerrar.
- `simulation.py`: loop fixo, hit detection e regra de 3 acertos.
- `ranking.py`: atualizar `player_stats` e consultas de ranking.

## Regras tecnicas
- Um processo async unico para estado em memoria local.
- Cada sala/partida com lock async para evitar corrida.
- Input rate-limit por conexao (ex.: max 30 msg/s).
- Timeout de reconexao por jogador (10s).
- Persistencia no fim da partida em transacao unica.

## Endpoints HTTP auxiliares
- `GET /health` para monitoramento.
- `GET /rooms` opcional para debug.
- `GET /ranking` opcional para tela web sem WS.
