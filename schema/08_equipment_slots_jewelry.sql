-- Add jewelry slots so the UI can show 14 slots: 7 body + 3 jewelry + 4 weapon.
-- Existing slots 1-11 (head, shoulders, chest, legs, feet, hands, waist, front_main, front_off, back_main, back_off).

INSERT OR IGNORE INTO equipment_slots (id, name) VALUES
    (12, 'neck'),
    (13, 'ring1'),
    (14, 'ring2');
