CREATE TABLE pastes (
    paste_id int PRIMARY KEY AUTO_INCREMENT,
    paste_slug varchar(16) NOT NULL COMMENT 'URL slug for the paste, must be unique',
    paste_expires datetime COMMENT 'When the paste expires, or NULL if it never expires',
    paste_type enum('paste', 'redirect') NOT NULL
        COMMENT 'What type of paste this is. If a paste, paste_content refers to the paste value itself. If a redirect, paste_content is a URL to redirect the user to.',
    paste_content text NOT NULL,
    CONSTRAINT pastes_paste_slug UNIQUE KEY (paste_slug),
    INDEX pastes_paste_expires (paste_expires)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
