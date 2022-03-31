CREATE DATABASE IF NOT EXISTS model_db;

USE model_db;

CREATE TABLE IF NOT EXISTS projects (
    project_name VARCHAR(255) PRIMARY KEY,
    description TEXT NOT NULL,
    create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)  ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS models (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(255) NOT NULL,
    laboratory VARCHAR(255) NOT NULL,
    facility VARCHAR(255) NOT NULL,
    beampath VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS deployments (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(255) NOT NULL,
    deploy_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asset_dir VARCHAR(255),
    asset_url VARCHAR(255),
    sha256  VARCHAR(255) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    model_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,
    FOREIGN KEY (model_id)
    REFERENCES models(model_id)
    ON UPDATE RESTRICT
)  ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS flows (
    flow_id VARCHAR(255) PRIMARY KEY,
    flow_name VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    deploy_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ON UPDATE RESTRICT,
    FOREIGN KEY (project_name)
    REFERENCES projects(project_name)
    ON UPDATE RESTRICT
) ENGINE=INNODB;


CREATE TABLE IF NOT EXISTS flow_to_deployments (
    flow_id VARCHAR(255) PRIMARY KEY,
    deployment_id INT NOT NULL,
    FOREIGN KEY (deployment_id)
    REFERENCES deployments(deployment_id)
    ON UPDATE RESTRICT,
) ENGINE=INNODB;