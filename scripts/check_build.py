import sqlite3
conn = sqlite3.connect("data/eso_build_genius.db")
bid = 13
print("Types in set_summary build 13:", conn.execute("SELECT type, COUNT(*) FROM set_summary WHERE game_build_id=? GROUP BY type", (bid,)).fetchall())
print("5pc filter:", conn.execute(
    "SELECT COUNT(*) FROM set_summary WHERE game_build_id=? AND set_max_equip_count=5 AND type IN ('crafted','dungeon','trial','overland','arena','pvp')", (bid,)
).fetchone())
print("monster:", conn.execute(
    "SELECT COUNT(*) FROM set_summary WHERE game_build_id=? AND type='monster' AND set_max_equip_count=2", (bid,)
).fetchone())
# Monster: how many have slot 1, slot 2, or multiple slots
for sid, sname in [(1, "head"), (2, "shoulder")]:
    n = conn.execute("""
      SELECT COUNT(DISTINCT s.game_id) FROM set_summary s
      JOIN set_item_slots sl ON sl.game_build_id=s.game_build_id AND sl.game_id=s.game_id AND sl.slot_id=?
      WHERE s.game_build_id=? AND s.type='monster'
    """, (sid, bid)).fetchone()[0]
    print("Monster with %s (slot %s): %s" % (sname, sid, n))
# Trial set names (for Aetherian Archive context)
trials = conn.execute(
    "SELECT set_name, game_id FROM set_summary WHERE game_build_id=? AND type='trial' ORDER BY set_name LIMIT 30",
    (bid,),
).fetchall()
print("Trial sets:", [t[0] for t in trials])
conn.close()
