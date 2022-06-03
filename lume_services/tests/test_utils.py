from functools import partial
from pydantic.json import custom_pydantic_encoder
import json
from types import FunctionType, MethodType
from typing import Callable
import pytest

from lume_services.utils import (
    JSON_ENCODERS,
    validate_and_compose_kwargs,
    CallableModel,
    ObjLoader,
    ObjType,
    get_callable_from_string,
)


def misc_fn(x):
    return x


class MiscClass:
    @staticmethod
    def _misc_static_method():
        return

    @classmethod
    def _misc_cls_method(cls):
        return cls

    def _misc_method(self):
        return


class TestJsonEncoders:

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("fn",),
        [
            (misc_fn,),
            pytest.param(misc_class._misc_method, marks=pytest.mark.xfail),
            (misc_class._misc_static_method,),
            pytest.param(misc_class._misc_cls_method, marks=pytest.mark.xfail),
        ],
    )
    def test_function_type(self, fn):
        encoder = {FunctionType: JSON_ENCODERS[FunctionType]}
        json_encoder = partial(custom_pydantic_encoder, encoder)

        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)
        callable_from_str = get_callable_from_string(loaded)

        assert fn == callable_from_str

    @pytest.mark.parametrize(
        ("fn",),
        [
            pytest.param(misc_class._misc_static_method, marks=pytest.mark.xfail),
            pytest.param(misc_fn, marks=pytest.mark.xfail),
            (misc_class._misc_method,),
            (misc_class._misc_cls_method,),
        ],
    )
    def test_method_type(self, fn):
        encoder = {MethodType: JSON_ENCODERS[MethodType]}
        json_encoder = partial(custom_pydantic_encoder, encoder)

        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)
        bound_callable = get_callable_from_string(loaded)

        assert fn == bound_callable(self.misc_class)

    @pytest.mark.parametrize(
        ("fn",),
        [
            (misc_class._misc_static_method,),
            (misc_fn,),
            (misc_class._misc_method,),
            (misc_class._misc_cls_method,),
        ],
    )
    def test_full_encoder(self, fn):
        json_encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)

        if isinstance(fn, (FunctionType,)):
            callable_from_str = get_callable_from_string(loaded)

            assert fn == callable_from_str

        elif isinstance(fn, (MethodType,)):
            bound_callable = get_callable_from_string(loaded)

            assert fn == bound_callable(self.misc_class)


class TestSignatureValidateAndCompose:
    def validate_kwarg_only():
        ...

    def validate_positional_only():
        ...

    def validate_mixed_kwarg_and_positional():
        ...

    def validate_var_positional():
        ...

    def validate_var_kwarg():
        ...

    def validate_mixed():
        ...


"""


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
"""


if __name__ == "__main__":
    json_test = TestJsonEncoders()
    json_test.test_function_type(misc_fn)

    misc_class = MiscClass()

    breakpoint()
