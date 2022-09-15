
CREATE TABLE model (
	model_id INTEGER NOT NULL AUTO_INCREMENT,
	created DATETIME DEFAULT now(),
	author VARCHAR(255) NOT NULL,
	laboratory VARCHAR(255) NOT NULL,
	facility VARCHAR(255) NOT NULL,
	beampath VARCHAR(255) NOT NULL,
	description VARCHAR(255) NOT NULL,
	PRIMARY KEY (model_id)
);
CREATE TABLE project (
	project_name VARCHAR(255) NOT NULL,
	description VARCHAR(255) NOT NULL,
	PRIMARY KEY (project_name)
);
CREATE TABLE deployment (
	deployment_id INTEGER NOT NULL AUTO_INCREMENT,
	version VARCHAR(255) NOT NULL,
	deploy_date DATETIME DEFAULT now(),
	package_import_name VARCHAR(255) NOT NULL,
	asset_dir VARCHAR(255),
	source VARCHAR(255) NOT NULL,
	sha256 VARCHAR(255) NOT NULL,
	image VARCHAR(255),
	is_live BOOL NOT NULL,
	model_id INTEGER NOT NULL,
	PRIMARY KEY (deployment_id),
	CONSTRAINT _sha256_unique UNIQUE (sha256),
	FOREIGN KEY(model_id) REFERENCES model (model_id)
);
CREATE TABLE flow (
	flow_id VARCHAR(255) NOT NULL,
	flow_name VARCHAR(255) NOT NULL,
	project_name VARCHAR(255) NOT NULL,
	deployment_id INTEGER NOT NULL,
	PRIMARY KEY (flow_id),
	FOREIGN KEY(project_name) REFERENCES project (project_name),
	FOREIGN KEY(deployment_id) REFERENCES deployment (deployment_id)
);
CREATE TABLE flow_of_flows (
	_id INTEGER NOT NULL AUTO_INCREMENT,
	parent_flow_id VARCHAR(255) NOT NULL,
	flow_id VARCHAR(255) NOT NULL,
	position INTEGER NOT NULL,
	PRIMARY KEY (_id),
	CONSTRAINT _flow_of_flow_entry UNIQUE (parent_flow_id, flow_id),
	FOREIGN KEY(parent_flow_id) REFERENCES flow (flow_id),
	FOREIGN KEY(flow_id) REFERENCES flow (flow_id)
);
