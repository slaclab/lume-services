
# Docker

Running tests in docker may be problematic with user. Must add this item to conf:
https://github.com/ClearcodeHQ/pytest-mysql/issues/62

```
echo -e '[mysqld]\nuser=root' > /etc/my.cnf
```


Require docker API version >=1.25

## pytest

Pytest tests the mysql commands using the system `mysqld` command in path. To use an alternative installation add `mysql_mysqld=/path/to/mysqld` to pytest.ini...

Has only been tested on 8.0.28



# Pydantic docker secrets:
https://pydantic-docs.helpmanual.io/usage/settings/


Preprocessing

* Boilerplate environment
- linear, functional,
- Tabular input style will be most common and useful


- Example custom thing, for example vcc_array
