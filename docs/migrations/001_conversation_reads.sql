-- Apply once to an existing CryptChat database before deploying unread badges.
-- This additive table stores only each user's last-read message ID.
CREATE TABLE IF NOT EXISTS conversation_reads (
    user_id INT NOT NULL,
    partner_id INT NOT NULL,
    last_read_message_id INT NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, partner_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES users(id) ON DELETE CASCADE
);
