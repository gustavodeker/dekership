from datetime import datetime

from ..db import get_conn


class RankingService:
    async def persist_match_result(
        self,
        match_uuid: str,
        winner_user_id: int,
        loser_user_id: int,
        end_reason: str,
        disconnect_loser: bool = False,
    ) -> None:
        now = datetime.utcnow()
        async with get_conn() as conn:
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE game_match SET winner_user_id = %s, loser_user_id = %s, end_reason = %s, status = 'finished', ended_at = %s WHERE match_uuid = %s",
                        (winner_user_id, loser_user_id, end_reason, now, match_uuid),
                    )

                    await cur.execute(
                        """
                        INSERT INTO player_stats (user_id, wins, losses, disconnects, updated_at)
                        VALUES (%s, 1, 0, 0, %s)
                        ON DUPLICATE KEY UPDATE wins = wins + 1, updated_at = VALUES(updated_at)
                        """,
                        (winner_user_id, now),
                    )

                    loser_disconnects = 1 if disconnect_loser else 0
                    await cur.execute(
                        """
                        INSERT INTO player_stats (user_id, wins, losses, disconnects, updated_at)
                        VALUES (%s, 0, 1, %s, %s)
                        ON DUPLICATE KEY UPDATE losses = losses + 1, disconnects = disconnects + VALUES(disconnects), updated_at = VALUES(updated_at)
                        """,
                        (loser_user_id, loser_disconnects, now),
                    )
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

    async def get_top_ranking(self, limit: int = 100) -> list[dict[str, int | str]]:
        query = (
            "SELECT u.id, u.usuario, s.wins, s.losses, s.disconnects "
            "FROM player_stats s "
            "JOIN usuario u ON u.id = s.user_id "
            "ORDER BY s.wins DESC, s.losses ASC "
            "LIMIT %s"
        )
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (limit,))
                rows = await cur.fetchall()
        return [
            {
                "user_id": int(r[0]),
                "usuario": str(r[1]),
                "wins": int(r[2]),
                "losses": int(r[3]),
                "disconnects": int(r[4]),
            }
            for r in rows
        ]

    async def get_user_stats(self, user_id: int) -> dict[str, int] | None:
        query = "SELECT wins, losses, disconnects FROM player_stats WHERE user_id = %s"
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id,))
                row = await cur.fetchone()
        if not row:
            return None
        return {"wins": int(row[0]), "losses": int(row[1]), "disconnects": int(row[2])}