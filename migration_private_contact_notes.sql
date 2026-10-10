-- Run once on an existing CryptChat database to enable private contact notes.
USE cryptchat;

CREATE TABLE IF NOT EXISTS contact_notes (
    owner_id INT NOT NULL,
    contact_id INT NOT NULL,
    ciphertext BLOB NOT NULL,
    nonce VARBINARY(12) NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (owner_id, contact_id),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES users(id) ON DELETE CASCADE
);
