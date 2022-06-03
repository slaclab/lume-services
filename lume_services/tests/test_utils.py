from functools import partial
from pydantic.json import custom_pydantic_encoder
import json
from types import FunctionType, MethodType
from typing import Callable
import pytest

from lume_services.utils import (
    JSON_ENCODERS,
    validate_and_compose_signature,
    CallableModel,
    ObjLoader,
    ObjType,
    get_callable_from_string,
)


def misc_fn(x, y=1, *args, **kwargs):
    pass


class MiscClass:
    @staticmethod
    def misc_static_method(x, y=1, *args, **kwargs):
        return

    @classmethod
    def misc_cls_method(cls, x, y=1, *args, **kwargs):
        return cls

    def misc_method(self, x, y=1, *args, **kwargs):
        return


class TestJsonEncoders:

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("fn",),
        [
            (misc_fn,),
            pytest.param(misc_class.misc_method, marks=pytest.mark.xfail(strict=True)),
            (misc_class.misc_static_method,),
            pytest.param(misc_class.misc_cls_method, marks=pytest.mark.xfail(strict=True)),
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
            pytest.param(misc_class.misc_static_method, marks=pytest.mark.xfail(strict=True)),
            pytest.param(misc_fn, marks=pytest.mark.xfail(strict=True)),
            (misc_class.misc_method,),
            (misc_class.misc_cls_method,),
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
            (misc_class.misc_static_method,),
            (misc_fn,),
            (misc_class.misc_method,),
            (misc_class.misc_cls_method,),
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

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("args","kwargs"),
        [
            pytest.param((5, 2, 1), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), ({"y": 2}), marks=pytest.mark.xfail(strict=True)),
            pytest.param((2,), ({"x": 2}), marks=pytest.mark.xfail(strict=True)),
            ((), ({"x": 2})),
            ((), {}),
        ],
    )
    def test_validate_kwarg_only(self, args, kwargs):

        def run(*, x: int = 4):
            pass

        returned_args, returned_kwargs = validate_and_compose_signature(run, *args, **kwargs)
        assert len(returned_args) == 0
        assert len(returned_kwargs) == len(kwargs)
        assert all([returned_kwargs[i] == kwargs[i] for i in returned_kwargs])
        # run
        run(*returned_args, **returned_kwargs)

    @pytest.mark.parametrize(
        ("args","kwargs"),
        [
            pytest.param((5,), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((2,), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), {}, marks=pytest.mark.xfail(strict=True)),
            ((2,), {}),
        ],
    )
    def test_validate_positional_only(self, args, kwargs):

        def run(x, /):
            pass

        returned_args, returned_kwargs = validate_and_compose_signature(run, *args, **kwargs)
        assert len(returned_kwargs) == 0
        assert len(returned_args) == len(args)

        # run
        run(*returned_args, **returned_kwargs)


    @pytest.mark.parametrize(
        ("args","kwargs"),
        [
            pytest.param((5,3,2,), {"x": 1}, marks=pytest.mark.xfail(strict=True)),
            ((2, 1, 0), {}),
            ((), {})
        ],
    )
    def test_validate_var_positional(self, args, kwargs):

        def run(*args):
            pass

        returned_args, returned_kwargs = validate_and_compose_signature(run, *args, **kwargs)
        assert len(returned_kwargs) == 0
        assert len(returned_args) == len(args)

        # run
        run(*returned_args, **returned_kwargs)

    @pytest.mark.parametrize(
        ("args","kwargs"),
        [
            pytest.param((5,), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((2,), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), {"x": 2, "y": 3}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), {}, marks=pytest.mark.xfail(strict=True)),
            ((2, 4,), {}),
            ((2,), {"y": 4, "extra": True}),
            ((2,), {"y": 4}),
            ((2,), {"y": 4, "z": 3}),
        ],
    )
    def test_validate_full_sig(self, args, kwargs):

        def run(x, /, y, z=4, *args, **kwargs):
            pass

        returned_args, returned_kwargs = validate_and_compose_signature(run, *args, **kwargs)

        # run
        run(*returned_args, **returned_kwargs)


    @pytest.mark.parametrize(
        ("args","kwargs"),
        [
            pytest.param((5, 1), {"y": 2}, marks=pytest.mark.xfail(strict=True)),
            ((2, 4,), {}),
            ((5,), {"y": 2})
        ],
    )
    def test_validate_classmethod(self, args, kwargs):

        returned_args, returned_kwargs = validate_and_compose_signature(self.misc_class.misc_cls_method, *args, **kwargs)
        self.misc_class.misc_cls_method(*returned_args, **returned_kwargs)

    







def TestCallableModel():

    def call(self):
        ...




"""



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
