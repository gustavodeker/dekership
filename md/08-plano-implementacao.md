# Plano de implementacao (ordem recomendada)

## Fase 1 - Banco
- Criar tabelas `game_room`, `game_match`, `player_stats`.
- Validar indices e chaves estrangeiras.
- Criar query de ranking por vitorias.

## Fase 2 - Servidor Python
- Implementar autenticacao WS por token de sessao.
- Implementar criar/listar/entrar sala.
- Iniciar partida automatica ao segundo jogador entrar.
- Implementar loop de jogo e regra de 3 hits.
- Persistir resultado no banco.

## Fase 3 - PHP/Frontend
- Criar tela lobby com lista de salas e botao criar sala.
- Integrar cliente WS no lobby e jogo.
- Atualizar perfil com `wins/losses/disconnects`.
- Atualizar ranking para fonte `player_stats`.

## Fase 4 - Validacao
- Testar 2 clientes simultaneos em rede local.
- Testar desconexao no meio da partida.
- Testar concorrencia de criacao/entrada de salas.
- Testar atualizacao de ranking apos varias partidas.

## Criterios de aceite
- Sala inicia automaticamente com 2 jogadores.
- Partida termina no terceiro acerto.
- Vencedor e perdedor persistidos corretamente.
- Perfil mostra vitorias e derrotas corretas.
- Ranking ordena por maior numero de vitorias.
