# Regras do jogo 1v1

## Regras fechadas
- Partida sempre com 2 jogadores.
- Movimento livre em 2 eixos dentro da arena.
- Nave sempre orientada pela posicao atual do cursor.
- Disparo ocorre no clique esquerdo.
- Projetil sai da posicao atual da nave e segue a direcao da mira.
- Cada acerto no oponente soma 1 hit.
- Vence quem atingir 3 hits primeiro.

## Inicio e fim
- Estado `waiting`: sala com 0 ou 1 jogador.
- Estado `ready`: sala com 2 jogadores.
- Estado `playing`: partida em andamento.
- Estado `finished`: vencedor definido.

## Condicoes de encerramento
- Vitoria por 3 hits.
- Desconexao de um jogador durante `playing`: derrota por abandono apos timeout de reconexao.
- Timeout de reconexao recomendado: 10 segundos.

## Estatisticas
- Vencedor: `wins + 1`.
- Perdedor: `losses + 1`.
- Abandono: `losses + 1` e `disconnects + 1`.
- Ranking principal: ordenacao por `wins` desc.
