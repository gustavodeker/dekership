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
  - Canvas/area de jogo (base `1366x768`)
  - Escala dinamica com proporcao fixa (fit por viewport, sem rolagem vertical)
  - HUD no header (`Partida`, status, `Voce` e `Oponente`)
  - Overlay central de inicio: `3`, `2`, `1`, `GO!` (GO por 1 segundo)
  - Input bloqueado ate fim do `GO!`
  - Overlay central ao encerrar partida: `Vitoria!` ou `Derrota!` + `Saindo em 3... 2... 1...`
  - Feedback de hit no centro: `Hit!` por 1s (verde para atacante, vermelho para alvo)
  - Hit stop curto no impacto (`55ms`)
  - Flash de impacto no alvo (`~110ms`): verde quando voce acerta, vermelho quando recebe
  - Knockback visual no alvo (`16px`, decaimento em `140ms`, sem alterar estado autoritativo)
  - Input bloqueado durante o countdown de saida
  - Countdown mostrado apenas 1 vez por `match_id` (nao repetir em recarregar/reconectar)
  - Movimento em 8 direcoes
  - Mira pelo mouse
  - Disparo no clique esquerdo
  - Projetil com cor por dono: verde (seu), vermelho (inimigo)
  - Obstaculos renderizados no mapa para cover e rotas
  - Nave renderizada por spritesheet direcional (`/web/assets/spritesheet_9x9_512.png`, 9x9, 81 frames)
  - Frame da nave selecionado por angulo da mira (mouse), sem rotacao continua da imagem
  - Escala de render da nave em 3x (156x156)
  - Nome dos dois jogadores renderizado acima da nave em tempo real
- Perfil:
  - Vitorias, derrotas, desconexoes
- Ranking:
  - Lista ordenada por vitorias
- Configuracoes:
  - Visivel apenas para admin
  - Ajuste de velocidade de projetil e movimento
  - Ajuste de vida (`hits_to_win`)
  - Ajuste de intervalo minimo entre disparos por clique (`fire_cooldown_ticks`)
  - Seletor de WebSocket ativo (`ws_mode`: `VPS` ou `Local`)
  - Ajuste de suavizacao visual (`render_smoothing` 0..1)
  - Ajuste de hitbox da nave e do projetil
  - Toggle para mostrar/ocultar linha de hitbox no cliente (`show_hitbox`)
  - Controle de privilegio admin por usuario

## Fluxo no cliente
1. Abrir WS e enviar `auth`.
2. Receber `room_list_result` automaticamente ao conectar.
3. Criar ou entrar em sala.
   - Se ja estiver em sala propria e clicar `Entrar` em outra, a sala atual e desfeita automaticamente.
   - Se criador clicar `Sair da sala`, sala e encerrada para todos.
4. Receber `match_start`.
5. Rodar countdown inicial (primeira vez do `match_id`) e liberar controle no fim do `GO!`.
6. Durante `playing`, enviar `player_input`.
7. Renderizar estados recebidos por `state`.
   - Incluir render de `obstacles` e colisao visual com cobertura.
   - Interpolar nave e projetil entre snapshots.
   - Parear projetil por `projectile_id` (nao por indice).
8. Ao `match_end`, mostrar overlay de resultado com countdown de saida e voltar para lobby.
9. Tratar `room_closed` para limpar estado local de sala (`dk_room_id`/`dk_match_id`) e atualizar lista.

## Controles do game
- `WASD` ou setas: mover
- Mouse: mirar
- Clique esquerdo: atirar
- Nave renderizada por spritesheet direcional (81 direcoes)
- Projetil verde para voce e vermelho para inimigo
- Nome do jogador acompanha a nave em tempo real

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
