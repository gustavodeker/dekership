# Administracao e configuracoes

## Perfil administrador
- Admin padrao: usuario `deker`.
- Controle persistido na tabela `game_admin`.
- Tela: `index.php?page=settings`.

## Configuracoes de gameplay
- `projectile_speed`: velocidade vertical do projetil.
- `movement_speed`: deslocamento horizontal por tick.
- `hits_to_win`: acertos necessarios para vencer (vida da partida).
- `fire_cooldown_ticks`: intervalo minimo entre disparos por clique (ticks da simulacao).
- `ws_mode`: seleciona endpoint WebSocket ativo (`vps` ou `local`).
- `render_smoothing`: fator de suavizacao visual no cliente (`0..1`).
- `player_hitbox_radius`: raio da hitbox da nave.
- `projectile_hitbox_radius`: raio da hitbox do projetil.
- `show_hitbox`: habilita/oculta linha de hitbox visivel no cliente (`1`/`0`).
- Persistencia em `game_settings`.

## Regras operacionais
- Apenas admin acessa a tela de configuracoes.
- Admin pode promover ou remover outro admin.
- Admin logado nao pode remover o proprio privilegio pela UI.
- Backend Python recarrega configuracoes em cache curto.

## Bootstrap automatico
- PHP cria `game_settings` e `game_admin` se nao existirem.
- Backend Python tambem garante o schema no startup.

## Tabelas
```sql
CREATE TABLE IF NOT EXISTS game_settings (
  setting_key VARCHAR(80) PRIMARY KEY,
  setting_value VARCHAR(80) NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP
);
```

```sql
CREATE TABLE IF NOT EXISTS game_admin (
  user_id INT(11) PRIMARY KEY,
  granted_by_user_id INT(11) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_game_admin_user FOREIGN KEY (user_id) REFERENCES usuario(id),
  CONSTRAINT fk_game_admin_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES usuario(id)
);
```
