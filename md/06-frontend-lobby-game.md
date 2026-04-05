# Frontend Lobby e Game (PHP + JS + Tailwind)

## Telas
- Lobby inicial (apos login):
  - Botao `Criar sala`
  - Lista de salas abertas com botao `Entrar`
- Sala:
  - Jogadores conectados
  - Status `Aguardando jogador` / `Partida iniciando`
- Game:
  - Canvas/area de jogo
  - HUD de hits (0 a 3)
  - Movimento em 8 direcoes
  - Mira pelo mouse
  - Disparo no clique esquerdo
- Perfil:
  - Vitorias, derrotas, desconexoes
- Ranking:
  - Lista ordenada por vitorias
- Configuracoes:
  - Visivel apenas para admin
  - Ajuste de velocidade de projetil e movimento
  - Controle de privilegio admin por usuario

## Fluxo no cliente
1. Abrir WS e enviar `auth`.
2. Receber `room_list_result` automaticamente ao conectar.
3. Criar ou entrar em sala.
4. Receber `match_start`.
5. Durante `playing`, enviar `player_input`.
6. Renderizar estados recebidos por `state`.
7. Ao `match_end`, mostrar resultado e voltar para lobby.

## Controles do game
- `WASD` ou setas: mover
- Mouse: mirar
- Clique esquerdo: atirar
- Nave renderizada com rotacao em tempo real

## Organizacao de arquivos sugerida
```text
web/lobby/lobby.php
web/lobby/lobby.js
web/lobby/lobby.css
web/game/game.php
web/game/game.js
web/profile/profile.php
web/ranking/ranking.php
web/settings.php
```

## Integracao Tailwind
- CSS estatico unico em `web/assets/app.css`.
- Lista de salas atualizada em tempo real via WS.
