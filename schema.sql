CREATE DATABASE IF NOT EXISTS cryptchat;
USE cryptchat;


-- Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    last_seen DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);


-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    ciphertext BLOB NOT NULL,
    nonce VARBINARY(12) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),

    INDEX idx_conversation (
        sender_id,
        receiver_id,
        created_at
    )
);


-- Connection requests
CREATE TABLE IF NOT EXISTS connection_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,

    status ENUM(
        'pending',
        'accepted',
        'rejected',
        'removed'
    ) NOT NULL DEFAULT 'pending',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),

    UNIQUE KEY unique_request (
        sender_id,
        receiver_id
    ),

    INDEX idx_receiver_status (
        receiver_id,
        status
    ),

    INDEX idx_sender_status (
        sender_id,
        status
    )
);


-- Blocked users
CREATE TABLE IF NOT EXISTS blocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blocker_id INT NOT NULL,
    blocked_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (blocker_id) REFERENCES users(id),
    FOREIGN KEY (blocked_id) REFERENCES users(id),

    UNIQUE KEY unique_block (
        blocker_id,
        blocked_id
    )
);

-- Per-user unread state; stores only message IDs, not message contents or read receipts.
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
