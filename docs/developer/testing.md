# Testing

LUME-services tests are an attempt to capture the networking behavior of the server-based services. The development evironment described in

## Configuration
The `pytest.ini` file at the root of the repository describes the port-forwarding behavior passed to the docker-compose file packaged [here](https://github.com/slaclab/lume-services/blob/main/lume_services/docker/files/docker-compose.yml){target=_blank}.


### Tests



Create subprocess for agent


All services spun up using docker compose

Env variables....

### Notes

Using docker-compose every time you execute tests is extremely costly. These could be refactored to optionally use persistent resources.
