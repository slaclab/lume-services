from typing import TextIO
from pytablewriter import MarkdownTableWriter
from lume_services.config import LUMEServicesSettings
import click


def get_configuration_info(
    settings: type,
) -> dict:
    env_vars = {"base": []}

    schema = settings.schema()
    prefix = (settings.Config.env_prefix,)
    delimiter = settings.Config.env_nested_delimiter

    def unpack_props(
        props,
        parent,
        env_vars=env_vars,
        prefix=prefix,
        delimiter=delimiter,
        schema=schema,
    ):

        for prop_name, prop in props.items():
            if "properties" in prop:
                unpack_props(
                    prop["properties"], prefix=f"{prefix}{delimiter}{prop_name}"
                )

            elif "allOf" in prop:

                sub_prop_reference = prop["allOf"][0]["$ref"]
                # prepare from format #/
                sub_prop_reference = sub_prop_reference.replace("#/", "")
                sub_prop_reference = sub_prop_reference.split("/")
                reference_locale = schema
                for reference in sub_prop_reference:
                    reference_locale = reference_locale[reference]

                unpack_props(
                    reference_locale["properties"],
                    parent=parent,
                    prefix=f"{prefix}{delimiter}{prop_name}",
                )

            else:
                default = prop.get("default")
                type_ = prop.get("type")

                env_vars[parent].append(
                    {
                        "name": f"{prefix}{delimiter}{prop_name}".upper(),
                        "default": default,
                        "type": type_,
                    }
                )

    # iterate over top level definitions
    for item_name, item in schema["properties"].items():

        env_name = list(item["env_names"])[0]

        if "allOf" in item:

            sub_prop_reference = item["allOf"][0]["$ref"]
            # prepare from format #/
            sub_prop_reference = sub_prop_reference.replace("#/", "")
            sub_prop_reference = sub_prop_reference.split("/")
            reference_locale = schema
            for reference in sub_prop_reference:
                reference_locale = reference_locale[reference]

            env_vars[item_name] = []
            unpack_props(
                reference_locale["properties"], prefix=env_name, parent=item_name
            )

        else:
            default = item.get("default")
            type_ = item.get("type")

            env_vars["base"].append(
                {"name": env_name.upper(), "type": type_, "default": default}
            )

    return env_vars


def build_table(info: dict, output_file: TextIO) -> None:

    headers = ["Name", "Type", "Default"]

    def build_value_matrix(env_list):
        return [[var["name"], var["type"], var["default"]] for var in env_list]

    # first base configuration
    base_writer = MarkdownTableWriter(
        table_name="Base Configuration",
        headers=headers,
        value_matrix=build_value_matrix(info["base"]),
    )

    base_writer.dump(output_file, close_after_write=False)

    output_file.write("\n\n")

    # files
    base_writer = MarkdownTableWriter(
        table_name="Filesystem Configuration",
        headers=headers,
        value_matrix=build_value_matrix(info["mounted_filesystem"]),
    )

    base_writer.dump(output_file, close_after_write=False)

    output_file.write("\n\n")

    # environment
    env_res_writer = MarkdownTableWriter(
        table_name="Environment Resolution",
        headers=headers,
        value_matrix=build_value_matrix(info["environment"]),
    )

    env_res_writer.dump(output_file, close_after_write=False)
    output_file.write("\n\n")

    # model db
    model_db_writer = MarkdownTableWriter(
        table_name="Model Database",
        headers=headers,
        value_matrix=build_value_matrix(info["model_db"]),
    )

    model_db_writer.dump(output_file, close_after_write=False)
    output_file.write("\n\n")

    # results db
    results_db_writer = MarkdownTableWriter(
        table_name="Results Database",
        headers=headers,
        value_matrix=build_value_matrix(info["results_db"]),
    )

    results_db_writer.dump(output_file, close_after_write=False)
    output_file.write("\n\n")

    # scheduler
    scheduling_writer = MarkdownTableWriter(
        table_name="Scheduling Service",
        headers=headers,
        value_matrix=build_value_matrix(info["prefect"]),
    )

    scheduling_writer.dump(output_file, close_after_write=False)
    output_file.write("\n")


@click.command()
@click.option("--output_filename", required=True, type=str)
def build_configuration_table(output_filename):
    info = get_configuration_info(LUMEServicesSettings)
    with open(output_filename, "w") as f:
        build_table(info, f)


@click.group()
def main():
    pass


main.add_command(build_configuration_table)


if __name__ == "__main__":
    main()
