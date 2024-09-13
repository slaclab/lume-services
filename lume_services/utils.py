import json
import hashlib
import inspect
import logging
import docker
import numpy as np
import pandas as pd

from importlib import import_module
from typing import Any, Callable, Generic, List, Optional, TypeVar
from types import FunctionType, MethodType
from pydantic import model_validator, ConfigDict, BaseModel, create_model, Field
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


def docker_api_version():
    client = docker.from_env()
    return client.api.version()["ApiVersion"]


def filter_keys_in_settings(dictionary: dict, settings_obj: BaseSettings) -> dict:
    """Utility function for checking the membership of dictionary keys in a settings
    class definition.

    Args:
        dictionary (dict): Dictionary to check
        settings_obj (BaseSettings): Settings object for composing

    """
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


def get_jsonable_dict(dictionary: dict):
    """Converts numpy arrays inside a dictionary to list items."""

    def convert_array_values(dictionary):
        """Convert array values to list so the dictionary is json serializable."""
        dictionary = {
            key: value.tolist() if isinstance(value, (np.ndarray,)) else value
            for key, value in dictionary.items()
        }
        # convert pandas dataframe to json
        dictionary = {
            key: value.to_json() if isinstance(value, (pd.DataFrame,)) else value
            for key, value in dictionary.items()
        }
        dictionary = {
            key: convert_array_values(value) if isinstance(value, (dict,)) else value
            for key, value in dictionary.items()
        }
        return dictionary

    return convert_array_values(dictionary)


def fingerprint_dict(dictionary: dict):
    """Create a hash for a dictionary

    Args:
        dictionary (dict): Dictionary for which to create a fingerprint hash.

    """

    dictionary = get_jsonable_dict(dictionary)

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
    # function/method type distinguished for class members
    # and not recognized as callables
    FunctionType: lambda x: f"{x.__module__}.{x.__qualname__}",
    MethodType: lambda x: f"{x.__module__}.{x.__qualname__}",
    Callable: lambda x: f"{x.__module__}.{type(x).__qualname__}",
    type: lambda x: f"{x.__module__}.{x.__name__}",
    # for encoding instances of the ObjType}
    ObjType: lambda x: f"{x.__module__}.{x.__class__.__qualname__}",
    np.ndarray: lambda x: json.dumps(x.tolist()),
    dict: lambda x: {
        key: (
            value if not isinstance(value, (np.ndarray)) else json.dumps(value.tolist())
        )
        for key, value in x.items()
    },
    pd.DataFrame: lambda x: x.to_json(),
}


def get_callable_from_string(callable: str, bind: Any = None) -> Callable:
    """Get callable from a string. In the case that the callable points to a bound
    method, the function returns a callable taking the bind instance as the first arg.

    Args:
        callable: String representation of callable abiding convention
             __module__:callable
        bind: Class to bind as self

    Returns:
        Callable
    """
    callable_split = callable.rsplit(".", 1)

    if len(callable_split) != 2:
        raise ValueError(f"Improperly formatted callable string: {callable_split}")

    module_name, callable_name = callable_split

    try:
        module = import_module(module_name)

    except ModuleNotFoundError:

        try:
            module_split = module_name.rsplit(".", 1)

            if len(module_split) != 2:
                raise ValueError(f"Unable to access: {callable}")

            module_name, class_name = module_split

            module = import_module(module_name)
            callable_name = f"{class_name}.{callable_name}"

        except ModuleNotFoundError as err:
            logger.error("Unable to import module %s", module_name)
            raise err

        except ValueError as err:
            logger.error(err)
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


class SignatureModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def build(self, *args, **kwargs):
        stored_kwargs = self.dict()

        stored_args = []
        if "args" in stored_kwargs:
            stored_args = stored_kwargs.pop("args")

        # adjust for positional
        args = list(args)
        n_pos_only = len(stored_args)
        positional_kwargs = []
        if len(args) < n_pos_only:
            stored_args[:n_pos_only] = args

        else:
            stored_args = args[:n_pos_only]
            positional_kwargs = args[n_pos_only:]

        stored_kwargs.update(kwargs)

        # exclude empty parameters
        stored_kwargs = {
            key: value
            for key, value in stored_kwargs.items()
            if not value == inspect.Parameter.empty
        }
        if len(positional_kwargs):
            for i, positional_kwarg in enumerate(positional_kwargs):

                stored_kwargs[self.kwarg_order[i]] = positional_kwarg

        return stored_args, stored_kwargs


def validate_and_compose_signature(callable: Callable, *args, **kwargs):
    # try partial bind to validate
    signature = inspect.signature(callable)
    bound_args = signature.bind_partial(*args, **kwargs)

    sig_kw = bound_args.arguments.get("kwargs", {})
    sig_args = bound_args.arguments.get("args", [])

    sig_kwargs = {}
    # Now go parameter by parameter and assemble kwargs
    for i, param in enumerate(signature.parameters.values()):

        if param.kind in [param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY]:
            # if param not bound use default/ compose field rep
            if not sig_kw.get(param.name):

                # create a field representation
                if param.default == param.empty:
                    sig_kwargs[param.name] = param.empty

                else:
                    sig_kwargs[param.name] = param.default

            else:
                sig_kwargs[param.name] = sig_kw.get(param.name)

            # assign via binding
            if param.name in bound_args.arguments:
                sig_kwargs[param.name] = bound_args.arguments[param.name]

    # create pydantic model
    pydantic_fields = {
        "args": (List[Any], Field(list(sig_args))),
        "kwarg_order": Field(list(sig_kwargs.keys()), exclude=True),
    }
    for key, value in sig_kwargs.items():
        if isinstance(value, (tuple,)):
            pydantic_fields[key] = (tuple, Field(None))

        elif value == inspect.Parameter.empty:
            pydantic_fields[key] = (inspect.Parameter.empty, Field(value))

        else:
            # assigning empty default
            if value is None:
                pydantic_fields[key] = (inspect.Parameter.empty, Field(None))

            else:
                pydantic_fields[key] = value

    model = create_model(
        f"Kwargs_{callable.__qualname__}", __base__=SignatureModel, **pydantic_fields
    )

    return model()


class CallableModel(BaseModel):
    callable: Callable
    signature: SignatureModel
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders=JSON_ENCODERS, extra="forbid")

    @model_validator(mode="before")
    @classmethod
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
                callable = get_callable_from_string(callable, bind=values.pop("bind"))

            else:
                callable = get_callable_from_string(callable)

        values["callable"] = callable

        # for reloading:
        kwargs = {}
        args = []
        if "args" in values:
            args = values.pop("args")

        if "kwargs" in values:
            kwargs = values.pop("kwargs")

        if "signature" in values:
            if "args" in values["signature"]:
                args = values["signature"].pop("args")

            # not needed during reserialization
            if "kwarg_order" in values["signature"]:
                values["signature"].pop("kwarg_order")

            if "kwargs" in values:
                kwargs = values["signature"]["kwargs"]

            else:
                kwargs = values["signature"]

        values["signature"] = validate_and_compose_signature(callable, *args, **kwargs)

        return values

    def __call__(self, *args, **kwargs):
        if kwargs is None:
            kwargs = {}

        fn_args, fn_kwargs = self.signature.build(*args, **kwargs)

        return self.callable(*fn_args, **fn_kwargs)


class ObjLoader(
    BaseModel, Generic[ObjType],
    arbitrary_types_allowed=True,
    json_encoders=JSON_ENCODERS,
):
    object: Optional[ObjType]
    loader: CallableModel = None
    object_type: Optional[type]

    @model_validator(mode="before")
    @classmethod
    def validate_all(cls, values):
        # inspect class init signature
        obj_type = cls.__fields__["object"].type_

        # adjust for re init from json
        if "loader" not in values:
            loader = CallableModel(callable=obj_type, **values)

        else:
            # if already-initialized callable, do nothing
            if isinstance(values["loader"], (CallableModel,)):
                loader = values["loader"]

            else:
                # validate loader callable is same as obj type
                if values["loader"].get("callable") is not None:
                    # unparameterized callable will handle parsing
                    callable = CallableModel(callable=values["loader"]["callable"])

                    if callable.callable is not obj_type:
                        raise ValueError(
                            "Provided loader of type %s. ObjLoader parameterized for \
                                %s",
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


def select_python_version(version: str) -> str:
    """Utility for selecting a python version given a version string formatted with
    a pin.

    Args:
        version (str): String rep of version with pin

    Returns:
        str: Sting rep of version to use

    Raises:
        ValueError: Unable to parse python version.

    """

    # if >=, use base
    if ">=" in version or "<=" in version or "=" in version:
        v = float(version.split("=")[1])

    elif ">" in version:
        v = float(version.replace(">", "")) + 0.1

    elif "<" in version:
        v = float(version.replace("<", "")) - 0.1

    else:
        raise ValueError("Cannot parse python version %s", version)

    return str(v)


def flatten_dict_for_query(dictionary: dict, level_key: str = None):
    """Flatten a dictionary of values for pymongo query"""

    flattened_dict = {}

    for key, value in dictionary.items():

        if level_key is not None:
            key = f"{level_key}.{key}"

        if isinstance(value, dict):
            value_dict = flatten_dict_for_query(value, level_key=key)
            flattened_dict.update(value_dict)

        else:
            flattened_dict[key] = value

    return flattened_dict
