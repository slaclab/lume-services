from functools import wraps
from typing import List
import logging

logger = logging.getLogger(__name__)


def validate_kwargs_exist(table, ignore: List[str] = []):
    """Wrapper for validating provided kwargs against a sqlalchemy table chema

    Args:
        table: Schema table to validate against
        ignore: List of kwargs to ignore
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            allowed_kwargs = [col.key for col in table.__table__.columns]

            unnecessary_kwargs = []

            # validate kwargs are members of the table
            for kwarg in kwargs:
                if kwarg not in allowed_kwargs and kwarg not in ignore:
                    unnecessary_kwargs.append(kwarg)

            if len(unnecessary_kwargs):
                raise ValueError(
                    f"Extra kwargs found in query for table {table.__tablename__}: \
                        {','.join(unnecessary_kwargs)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
