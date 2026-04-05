# Sequencia de execucao oficial

1. Banco
- Executar `BANCO/migrations/001_1v1_schema.sql` na VPS.
- Validar tabelas: `game_room`, `game_match`, `player_stats`.
- Se houver `metadata lock` na VPS, liberar sessoes presas antes de reaplicar DDL.

2. Configuracao
- Manter `.env` na raiz.
- Definir `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`, `WS_URL`.
- Valor atual de teste: `WS_URL=ws://192.168.1.9:8766/ws`.

3. Backend Python
- Criar/ativar `.venv`.
- Instalar `requirements.txt`.
- Subir `uvicorn server.app:app --host 0.0.0.0 --port 8766`.

4. PHP/Frontend
- Subir app PHP local.
- Login em `index.php?page=login`.
- Lobby em `index.php?page=lobby`.
- Nao usar rotas legadas de `game/`; elas redirecionam para o fluxo novo.

5. Validacao
- 2 clientes na mesma sala.
- Inicio automatico com 2 jogadores.
- Countdown de inicio (`3,2,1,GO!`) aparece so uma vez por partida.
- Durante countdown/GO, movimento e tiro ficam bloqueados.
- Fim no terceiro hit.
- Ranking/perfil atualizados em `player_stats`.
- Se o navegador mantiver estado antigo, limpar `localStorage` (`dk_room_id`, `dk_match_id`) e recarregar.
