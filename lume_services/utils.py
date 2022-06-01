import json
import hashlib
import inspect
import logging
from importlib import import_module
from pydantic import BaseSettings
from typing import Any, Callable, Dict, Generic, Optional, TypeVar
from types import FunctionType
from pydantic import (
    BaseModel,
    root_validator,
    validate_arguments,
)
from pydantic.generics import GenericModel

logger = logging.getLogger(__name__)


def filter_keys_in_settings(dictionary: dict, settings_obj: BaseSettings):
    """Utility function for checking the membership of dictionary keys in a settings
    class definition."""
    not_in_settings = [
        key for key in dictionary.keys() if key not in settings_obj.attributes
    ]
    in_settings = [
        key for key in dictionary.keys() if key not in settings_obj.attributes
    ]

    if len(not_in_settings):
        logger.warning(
            "Key %s not found in settings. Allowed keys are for %s are %s",
            ",".join(not_in_settings),
            settings_obj.class_name,
            ",".join(settings_obj.attributes),
        )

    return {key: value for key, value in dictionary.items() if key in in_settings}


def fingerprint_dict(dictionary: dict):

    hasher = hashlib.md5()
    hasher.update(json.dumps(dictionary).encode("utf-8"))
    return hasher.hexdigest()


def flatten_dict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [(k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)


ObjType = TypeVar("ObjType")


JSON_ENCODERS = {
    FunctionType: lambda x: f"{x.__module__}:{x.__name__}",
    # for encoding functions
    Callable: lambda x: f"{x.__module__}:{type(x).__name__}",
    # for encoding a type
    type: lambda x: f"{x.__module__}:{x.__name__}",
    # for encoding instances of the ObjType}
    ObjType: lambda x: f"{x.__module__}:{x.__class__.__name__}",
}


@validate_arguments(config={"arbitrary_types_allowed": True})
def validate_and_compose_kwargs(signature: inspect.Signature, kwargs: Dict[str, Any]):
    required_kwargs = [
        kwarg.name
        for kwarg in signature.parameters.values()
        if (kwarg.POSITIONAL_OR_KEYWORD or kwarg.KEYWORD_ONLY)
        and kwarg.default is inspect.Parameter.empty
    ]

    if any([required_kwarg not in kwargs.keys() for required_kwarg in kwargs.keys()]):
        raise ValueError(
            "All required kwargs not provided: %s", ", ".join(required_kwargs)
        )

    # check (kwarg.VAR_KEYWORD and kwarg.default is inspect.Parameter.empty) is not
    # empty **kwargs
    sig_kwargs = {
        kwarg.name: kwarg.default
        for kwarg in signature.parameters.values()
        if (kwarg.POSITIONAL_OR_KEYWORD or kwarg.KEYWORD_ONLY)
        and not kwarg.kind == inspect.Parameter.VAR_KEYWORD
    }

    # validate kwargs
    if any([kwarg not in sig_kwargs.keys() for kwarg in kwargs.keys()]):
        raise ValueError(
            "Kwargs must be members of function signature. Accepted kwargs \
                are: %s, Provided: %s",
            ", ".join(sig_kwargs.keys()),
            ", ".join(kwargs.keys()),
        )

    sig_kwargs.update(kwargs)

    return sig_kwargs


class CallableModel(BaseModel):
    callable: Callable
    kwargs: dict

    class Config:
        arbitrary_types_allowed = True
        json_encoders = JSON_ENCODERS

    @root_validator(pre=True)
    def validate_all(cls, values):
        fn = values.pop("callable")

        if not isinstance(
            fn,
            (
                str,
                Callable,
            ),
        ):
            raise ValueError(
                "Callable must be object or a string. Provided %s", type(fn)
            )

        # parse string to callable
        if isinstance(fn, (str,)):

            # for function loading
            module_name, fn_name = fn.rsplit(":", 1)
            fn = getattr(import_module(module_name), fn_name)

        sig = inspect.signature(fn)

        # for reloading:
        if values.get("kwargs") is not None:
            values = values["kwargs"]

        kwargs = validate_and_compose_kwargs(sig, values)

        return {"callable": fn, "kwargs": kwargs}

    def __call__(self, **kwargs):
        return self.callable(**{**self.kwargs, **kwargs})


class ObjLoader(
    GenericModel,
    Generic[ObjType],
    arbitrary_types_allowed=True,
    json_encoders=JSON_ENCODERS,
):
    object: Optional[ObjType]
    loader: CallableModel = None
    object_type: Optional[type]

    @root_validator(pre=True)
    def validate_all(cls, values):
        # inspect class init signature
        obj_type = cls.__fields__["object"].type_

        # adjust for re init from json
        if "loader" not in values:
            loader = CallableModel(callable=obj_type, **values)

        else:
            print("Here")
            # validate loader callable is same as obj type
            if isinstance(values["loader"], (CallableModel,)):
                loader = values["loader"]

            elif values["loader"].get("callable") is not None:
                # unparameterized callable will handle parsing
                callable = CallableModel(callable=values["loader"]["callable"])

                if callable.callable is not obj_type:
                    raise ValueError(
                        "Provided loader of type %s. ObjLoader parameterized for %s",
                        callable.callable.__name__,
                        obj_type,
                    )

                # opt for obj type
                values["loader"].pop("callable")

                # re-init drop callable from loader vals to use new instance
                loader = CallableModel(callable=obj_type, **values["loader"])

        # update the class json encoders. Will only execute on initial type construction
        if obj_type not in cls.__config__.json_encoders:
            cls.__config__.json_encoders[obj_type] = cls.__config__.json_encoders.pop(
                ObjType
            )
        return {"object_type": obj_type, "loader": loader}

    def load(self, store: bool = False):
        # store object reference on loader
        if store:
            self.object = self.loader.call()
            return self.object

        # return loaded object w/o storing
        else:
            return self.loader()
