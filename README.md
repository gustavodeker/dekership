# Dekership 1v1

## Estrutura
- `server/`: FastAPI + WebSocket + regra autoritativa
- `web/`: login, lobby, game, perfil, ranking e APIs PHP
- `BANCO/migrations/001_1v1_schema.sql`: schema 1v1

## Controles
- Movimento: `WASD` ou setas
- Mira: cursor do mouse
- Tiro: clique esquerdo
- Nave aponta em tempo real para o cursor
- Nome de cada jogador aparece acima da nave em tempo real
- Projetil segue a direcao da mira

## UX de partida
- Inicio: overlay central `3`, `2`, `1`, `GO!`, com controle bloqueado ate o fim.
- Encerramento: overlay central `Vitoria!` ou `Derrota!` com `Saindo em 3... 2... 1...`, depois retorno ao lobby.

## Subida local
1. Copiar `.env.example` para `.env`
2. Aplicar `BANCO/migrations/001_1v1_schema.sql`
3. Instalar `requirements.txt`
4. Subir `uvicorn server.app:app --host 0.0.0.0 --port 8766`
5. Servir a raiz no PHP/Nginx e abrir `index.php?page=login`

## Requisitos de auth
- tabela `usuario`
- coluna de token configurável por `.env`
- credenciais lidas por `AUTH_*`
