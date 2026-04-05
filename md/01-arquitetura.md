# Arquitetura alvo 1v1

## Componentes
- PHP: login, cadastro, sessao, lobby e telas HTML.
- Python (FastAPI/WebSocket): matchmaking, sala, loop de partida e regra do jogo.
- MariaDB (VPS): usuarios, partidas, estatisticas e ranking.
- MariaDB (admin): `game_settings` e `game_admin`.
- JS/CSS: UI lobby/game e cliente WebSocket.

## Fluxo ponta a ponta
1. Usuario autentica no PHP (sessao atual).
2. Lobby carrega lista de salas abertas.
3. Usuario cria sala ou entra em sala existente.
4. Ao entrar 2 jogadores na mesma sala, servidor inicia partida.
5. Servidor calcula estado do jogo e envia snapshots para os 2 clientes.
6. Ao fim da partida, servidor grava vencedor/perdedor e atualiza estatisticas.
7. Perfil e ranking leem dados agregados no MariaDB.
8. Admin altera configuracoes de gameplay e privilegios via tela PHP.

## Fronteira de responsabilidade
- PHP nao valida regra de batalha.
- Cliente nao define resultado.
- Python e autoritativo para hit, vida e vitoria.
- Banco grava apenas eventos finais validados pelo servidor Python.
- Admin PHP grava configuracoes que o backend Python consome em tempo de execucao.

## Topologia local (Windows + rede local)
- App PHP: `http://<ip-local>:8080` (ex.: servidor embutido do PHP).
- WS Python: `ws://<ip-local>:8765/ws`.
- MariaDB remoto na VPS usando credenciais ja existentes.
