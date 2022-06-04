import json
import hashlib
import inspect
import logging
import copy
from importlib import import_module
from pydantic import BaseSettings
from typing import Any, Callable, Generic, Optional, Tuple, TypeVar
from types import FunctionType, MethodType
from pydantic import (
    BaseModel,
    root_validator,
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
    FunctionType: lambda x: f"{x.__module__}:{x.__qualname__}",
    MethodType: lambda x: f"{x.__module__}:{x.__qualname__}",
    Callable: lambda x: f"{x.__module__}:{type(x).__qualname__}",
    type: lambda x: f"{x.__module__}:{x.__name__}",
    # for encoding instances of the ObjType}
    ObjType: lambda x: f"{x.__module__}:{x.__class__.__qualname__}",
}


def get_callable_from_string(callable: str, bind: Any = None) -> Callable:
    """Get callable from a string. In the case that the callable points to a bound method,
    the function returns a callable taking the bind instance as the first arg.

    Args:
        callable: String representation of callable abiding convention
             __module__:callable

    Returns:
        Callable
    """
    callable_split = callable.rsplit(":")

    if len(callable_split) != 2:
        raise ValueError(f"Improperly formatted callable string: {callable_split}")

    module_name, callable_name = callable_split

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as err:
        logger.error("Unable to import module %s", module_name)
        raise err

    # construct partial in case of bound method
    if "." in callable_name:
        bound_class, callable_name = callable_name.rsplit(".")

        try:
            bound_class = getattr(module, bound_class)
        except Exception as e:
            logger.error("Unable to get %s from %s", bound_class, module_name)
            raise e

        # require right partial for assembly of callable
        # https://funcy.readthedocs.io/en/stable/funcs.html#rpartial
        def rpartial(func, *args):
            return lambda *a: func(*(a + args))

        callable = getattr(bound_class, callable_name)
        params = inspect.signature(callable).parameters

        # check bindings
        is_bound = params.get("self", None) is not None
        if not is_bound and bind is not None:
            raise ValueError("Cannot bind %s to %s.", callable_name, bind)

        # bound, return partial
        if bind is not None:
            if not isinstance(bind, (bound_class,)):
                raise ValueError(
                    "Provided bind %s is not instance of %s",
                    bind,
                    bound_class.__qualname__,
                )

        if is_bound and isinstance(callable, (FunctionType,)) and bind is None:
            callable = rpartial(getattr, callable_name)

        elif is_bound and isinstance(callable, (FunctionType,)) and bind is not None:
            callable = getattr(bind, callable_name)

    else:
        if bind is not None:
            raise ValueError("Cannot bind %s to %s.", callable_name, type(bind))

        try:
            callable = getattr(module, callable_name)
        except Exception as e:
            logger.error("Unable to get %s from %s", callable_name, module_name)
            raise e

    return callable


def validate_partial_signature(callable: Callable, *args, **kwargs):
    signature = inspect.signature(callable)
    bound_sig = signature.bind_partial(*args, **kwargs)

    return bound_sig.args, bound_sig.kwargs


def validate_and_compose_signature(callable: Callable, *args, **kwargs):

    signature = inspect.signature(callable)
    bound_sig = signature.bind(*args, **kwargs)

    return bound_sig.args, bound_sig.kwargs


class CallableModel(BaseModel):
    callable: Callable
    args: Tuple
    kwargs: Optional[dict]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = JSON_ENCODERS

    @root_validator(pre=True)
    def validate_all(cls, values):
        callable = values.pop("callable")

        if not isinstance(
            callable,
            (
                str,
                Callable,
            ),
        ):
            raise ValueError(
                "Callable must be object or a string. Provided %s", type(callable)
            )

        # parse string to callable
        if isinstance(callable, (str,)):

            # for function loading
            if "bind" in values:
                callable = get_callable_from_string(callable, bind=values["bind"])

            else:
                callable = get_callable_from_string(callable)

        # for reloading:
        kwargs = {}
        args = ()
        if "args" in values:
            args = values.pop("args")

        if "kwargs" in values:
            kwargs = values["kwargs"]
        else:
            # use remaining values as kwargs
            kwargs = values

        args, kwargs = validate_partial_signature(callable, *args, **kwargs)

        return {"callable": callable, "args": args, "kwargs": kwargs}

    def __call__(self, *args, **kwargs):
        # Args will override positions in self.args
        if len(self.args) > len(args):
            args = args + self.args[len(args) :]

        if kwargs is None:
            kwargs = {}

        # update stored kwargs
        if self.kwargs is not None:
            base_kwargs = copy.copy(kwargs)
            kwargs = self.kwargs
            kwargs.update(base_kwargs)

        args, kwargs = validate_and_compose_signature(self.callable, *args, **kwargs)
        return self.callable(*args, **kwargs)


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
