from pydantic import BaseSettings


class LUMESettings(BaseSettings):
    """Base class for enforcing common prefix on all LUMESettings"""

    class Config:
        env_prefix = "LUME_"
