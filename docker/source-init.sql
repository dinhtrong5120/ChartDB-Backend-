CREATE USER IF NOT EXISTS 'chartdb_reader'@'%' IDENTIFIED BY 'reader';
GRANT SELECT ON chartdb_source.* TO 'chartdb_reader'@'%';
FLUSH PRIVILEGES;

CREATE TABLE chartdb_source.users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NULL COMMENT 'Visible name',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chartdb_source.projects (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    owner_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id) REFERENCES chartdb_source.users(id),
    INDEX idx_projects_owner_name (owner_id, name)
);

CREATE VIEW chartdb_source.project_owners AS
SELECT p.id AS project_id, u.email FROM chartdb_source.projects p JOIN chartdb_source.users u ON u.id = p.owner_id;

