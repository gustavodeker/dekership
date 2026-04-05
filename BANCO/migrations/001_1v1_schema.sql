CREATE TABLE IF NOT EXISTS game_room (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  room_uuid CHAR(36) NOT NULL UNIQUE,
  name VARCHAR(80) NOT NULL,
  status ENUM('waiting','playing','closed') NOT NULL DEFAULT 'waiting',
  created_by_user_id INT(11) NOT NULL,
  created_at DATETIME NOT NULL,
  started_at DATETIME NULL,
  closed_at DATETIME NULL,
  KEY idx_room_status (status),
  KEY idx_room_created_by (created_by_user_id),
  CONSTRAINT fk_room_creator FOREIGN KEY (created_by_user_id) REFERENCES usuario(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS game_match (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  match_uuid CHAR(36) NOT NULL UNIQUE,
  room_id BIGINT NOT NULL,
  player_bottom_id INT(11) NOT NULL,
  player_top_id INT(11) NOT NULL,
  winner_user_id INT(11) NULL,
  loser_user_id INT(11) NULL,
  end_reason ENUM('3_hits','disconnect','forfeit') NULL,
  status ENUM('playing','finished') NOT NULL DEFAULT 'playing',
  started_at DATETIME NOT NULL,
  ended_at DATETIME NULL,
  KEY idx_match_status (status),
  KEY idx_match_winner (winner_user_id),
  KEY idx_match_started (started_at),
  CONSTRAINT fk_match_room FOREIGN KEY (room_id) REFERENCES game_room(id),
  CONSTRAINT fk_match_bottom FOREIGN KEY (player_bottom_id) REFERENCES usuario(id),
  CONSTRAINT fk_match_top FOREIGN KEY (player_top_id) REFERENCES usuario(id),
  CONSTRAINT fk_match_winner FOREIGN KEY (winner_user_id) REFERENCES usuario(id),
  CONSTRAINT fk_match_loser FOREIGN KEY (loser_user_id) REFERENCES usuario(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player_stats (
  user_id INT(11) PRIMARY KEY,
  wins INT(11) NOT NULL DEFAULT 0,
  losses INT(11) NOT NULL DEFAULT 0,
  disconnects INT(11) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL,
  KEY idx_stats_wins (wins),
  CONSTRAINT fk_stats_user FOREIGN KEY (user_id) REFERENCES usuario(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;