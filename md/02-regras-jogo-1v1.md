# Regras do jogo 1v1

## Regras fechadas
- Partida sempre com 2 jogadores.
- Movimento livre em 2 eixos dentro da arena.
- Nave sempre orientada pela posicao atual do cursor.
- Disparo ocorre no clique esquerdo.
- Projetil sai da posicao atual da nave e segue a direcao da mira.
- Obstaculos fixos no mapa bloqueiam movimento da nave.
- Obstaculos bloqueiam projeteis (cobertura).
- Cada acerto no oponente soma 1 hit.
- Vence quem atingir 3 hits primeiro.
- Hitbox de acerto entre nave e projetil e circular.
- Hitbox da nave e do projetil sao configuradas separadamente.

## Inicio e fim
- Estado `waiting`: sala com 0 ou 1 jogador.
- Estado `ready`: sala com 2 jogadores.
- Estado `playing`: partida em andamento.
- Estado `finished`: vencedor definido.
- Ao receber `match_start`, exibir countdown visual `3, 2, 1, GO!` no centro.
- Durante countdown + `GO!` (1s), input do jogador fica bloqueado.
- Countdown aparece 1 vez por `match_id` (nao repetir em recarga/reconexao da mesma partida).

## Condicoes de encerramento
- Vitoria por 3 hits.
- Desconexao de um jogador durante `playing`: derrota por abandono apos timeout de reconexao.
- Timeout de reconexao recomendado: 10 segundos.

## Estatisticas
- Vencedor: `wins + 1`.
- Perdedor: `losses + 1`.
- Abandono: `losses + 1` e `disconnects + 1`.
- Ranking principal: ordenacao por `wins` desc.
