from lume_services import config
from lume_model.variables import Variable
from prefect import task
from typing import Dict, Any
import logging
import os
import json
import copy


logger = logging.getLogger(__name__)


@task(name="check_local_execution")
def check_local_execution():
    from lume_services.config import _settings

    if _settings.backend == "local":
        return True
    else:
        return False


@task(name="configure_lume_services")
def configure_lume_services():
    """Configure LUME-services using environment variables. This task must be included
    in any workflow using common database services.

    """
    logger.debug("Configuring environment using %s", json.dumps(dict(os.environ)))
    config.configure()


@task(name="prepare_lume_model_variables")
def prepare_lume_model_variables(
    value_map: Dict[str, Any], variables: Dict[str, Variable]
) -> Dict[str, Variable]:
    """Utility task for translating parameter values to LUME-model variables.

    Args:
        value_map (Dict[str, Any]): Dictionary mapping variable name to value.
        variables (Dict[str, Variable]): Dictionary mapping variable name to LUME-model
            variable object.

    Returns:
        variables (Dict[str, Variable]): Formatted LUME-model variables.

    Raises:
        ValueError: Variable name passed to value_map is not found in model variables.

    """
    # Use deepcopy because don't want to transform global vars
    variables = copy.deepcopy(variables)

    for var_name in value_map:
        if var_name not in variables:
            raise ValueError(
                "Variable name passed to value_map %s not found in model variables. \
                Model variables are %s",
                var_name,
                ",".join(list(variables.keys())),
            )
        variables[var_name].value = value_map[var_name]

    missing_values = [
        var_name for var_name in variables.keys() if var_name not in value_map
    ]
    logger.warning(
        "No value provided for: %s. Will assign variable default to value.",
        ", ".join(missing_values),
    )
    for var_name in missing_values:
        variables[var_name].value = variables[var_name].default

    return variables
