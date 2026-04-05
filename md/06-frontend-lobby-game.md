# Frontend Lobby e Game (PHP + JS + Tailwind)

## Telas
- Lobby inicial (apos login):
  - Botao `Criar sala`
  - Botao `Sair da sala`
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
  - Obstaculos renderizados no mapa para cover e rotas
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
   - Se ja estiver em sala propria e clicar `Entrar` em outra, a sala atual e desfeita automaticamente.
   - Se criador clicar `Sair da sala`, sala e encerrada para todos.
4. Receber `match_start`.
5. Durante `playing`, enviar `player_input`.
6. Renderizar estados recebidos por `state`.
   - Incluir render de `obstacles` e colisao visual com cobertura.
7. Ao `match_end`, mostrar resultado e voltar para lobby.
8. Tratar `room_closed` para limpar estado local de sala (`dk_room_id`/`dk_match_id`) e atualizar lista.

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
