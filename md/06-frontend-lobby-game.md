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
- Perfil:
  - Vitorias, derrotas, desconexoes
- Ranking:
  - Lista ordenada por vitorias

## Fluxo no cliente
1. Abrir WS e enviar `auth`.
2. Solicitar `room_list`.
3. Criar ou entrar em sala.
4. Receber `match_start`.
5. Durante `playing`, enviar `player_input`.
6. Renderizar estados recebidos por `state`.
7. Ao `match_end`, mostrar resultado e voltar para lobby.

## Organizacao de arquivos sugerida
```text
web/lobby/lobby.php
web/lobby/lobby.js
web/lobby/lobby.css
web/game/game.php
web/game/game.js
web/profile/profile.php
web/ranking/ranking.php
```

## Integracao Tailwind
- Compilar CSS do Tailwind para arquivo estatico unico.
- Evitar CDN em producao.
- Definir componentes utilitarios para cards de sala, tabela e HUD.
