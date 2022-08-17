# Model database service

The model database stores references to registered flows, model metadata, ...

Sqlalchemy comments...
Schema is defined using the sqlalchemy API in


Sqlalchemy can be configured to use a number of different [dialects](https://docs.sqlalchemy.org/en/14/dialects/). The database implementation in `lume_services/services/models/db/db.py` defaults to using a `mysql` connection, as indicated with the `dialect_str="mysql+pymysql"` attribute on the ModelDBConfig object. Additional dialects can be accomodated by assigning this dialect string.


## Updating the model schema
On any changes to the schema, the database init script for the docker-compose must be updated.

From the repository root run,
```
python scripts/update_docker_compose_schema.py build-docker-compose-schema
```

This will automatically render the schema file in `lume_services/docker/files/model-db-init.sql`. Now, you can add this file updated file to the git repository.




## Conda channel

The conda channel must be updated to provide the packages ahead of time


https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html
