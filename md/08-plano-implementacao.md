# Plano de implementacao (ordem recomendada)

## Fase 1 - Banco
- Concluido: criadas `game_room`, `game_match`, `player_stats`.
- Concluido: indices principais criados para status, criador, vencedor e ranking.
- Pendente opcional: reintroduzir FKs na VPS quando nao houver `metadata lock`.

## Fase 2 - Servidor Python
- Concluido: autenticacao WS por token de sessao PHP.
- Concluido: criar/listar/entrar sala.
- Concluido: inicio automatico ao segundo jogador entrar.
- Concluido: loop de jogo e regra de vitoria por vida configuravel.
- Concluido: persistencia de resultado no banco.
- Concluido: push automatico da lista de salas.
- Concluido: leitura dinamica de configuracoes de gameplay.

## Fase 3 - PHP/Frontend
- Concluido: lobby com criar sala e lista de salas.
- Concluido: cliente WS no lobby e no jogo.
- Concluido: perfil com `wins/losses/disconnects`.
- Concluido: ranking lendo `player_stats`.
- Concluido: redirecionamento dos entrypoints legados para o fluxo novo.
- Concluido: cadastro PHP.
- Concluido: tela administrativa de configuracoes e privilegios.

## Fase 4 - Validacao
- Em andamento: teste com 2 clientes simultaneos em rede local.
- Pendente: validar desconexao no meio da partida.
- Pendente: validar concorrencia de criacao/entrada de salas com repeticao.
- Pendente: validar atualizacao de ranking apos varias partidas.
- Pendente: validar alteracao de `projectile_speed` e `movement_speed` com novas partidas.
- Pendente: validar promocao/rebaixamento de admin.

## Criterios de aceite
- Sala inicia automaticamente com 2 jogadores.
- Partida termina ao atingir `hits_to_win`.
- Vencedor e perdedor persistidos corretamente.
- Perfil mostra vitorias e derrotas corretas.
- Ranking ordena por maior numero de vitorias.

## Estado atual
- Fluxo alvo: `login -> lobby -> room_create/room_join -> match_start -> game`.
- Porta ativa de teste local: `8766`.
- Cliente so navega do lobby para o game no evento `match_start`.
- Servidor reenvia `match_start` quando o jogador reconecta em sala `playing`.
