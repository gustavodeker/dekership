# Regras do jogo 1v1

## Regras fechadas
- Partida sempre com 2 jogadores.
- Movimento livre em 2 eixos dentro da arena.
- Nave sempre orientada pela posicao atual do cursor.
- Disparo ocorre no clique esquerdo.
- Skill de mina no atalho `1`.
- Projetil sai da posicao atual da nave e segue a direcao da mira.
- Mina e fixa no mapa apos ser solta.
- Contato de nave inimiga com mina causa 1 hit.
- Projetil pode acertar mina inimiga e reduzir vida da mina.
- Mina e destruida ao atingir `mine_hits_to_destroy`.
- Obstaculos fixos no mapa bloqueiam movimento da nave.
- Obstaculos bloqueiam projeteis (cobertura).
- Cada acerto no oponente soma 1 hit.
- Vence quem atingir a vida configurada (`hits_to_win`) primeiro.
- Hitbox de acerto entre nave e projetil e circular.
- Hitbox da nave e do projetil sao configuradas separadamente.
- Hitbox da mina e configuravel.
- Cooldown da mina e configuravel (`mine_cooldown_ticks`, padrao 5s em 20 TPS).

## Inicio e fim
- Estado `waiting`: sala com 0 ou 1 jogador.
- Estado `ready`: sala com 2 jogadores.
- Estado `playing`: partida em andamento.
- Estado `finished`: vencedor definido.
- Ao receber `match_start`, exibir countdown visual `3, 2, 1, GO!` no centro.
- Durante countdown + `GO!` (1s), input do jogador fica bloqueado.
- Countdown aparece 1 vez por `match_id` (nao repetir em recarga/reconexao da mesma partida).

## Condicoes de encerramento
- Vitoria ao atingir `hits_to_win`.
- Desconexao de um jogador durante `playing`: derrota por abandono apos timeout de reconexao.
- Timeout de reconexao recomendado: 10 segundos.

## Estatisticas
- Vencedor: `wins + 1`.
- Perdedor: `losses + 1`.
- Abandono: `losses + 1` e `disconnects + 1`.
- Ranking principal: ordenacao por `wins` desc.
