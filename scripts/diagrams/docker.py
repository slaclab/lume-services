import yaml
import os.path
import click

from diagrams import Cluster, Diagram, Edge

from diagrams.onprem.container import Docker
from diagrams.onprem.compute import Server
from diagrams.generic.storage import Storage as FileStorage

from lume_services.docker.files import DOCKER_COMPOSE


def clean_mapped_value(val, show_defaults):

    if ":" in val:
        parts = val.split(":")

        if "$" in parts[0]:
            # remove bracket
            parts[0] = parts[0].replace("{", "")
            parts[1] = parts[1].replace("-", "").replace("}", "")

        if len(parts) == 2:
            return f"{parts[0]}: {parts[1]}"

        # has defaults
        elif len(parts) == 3:
            if show_defaults:
                return f"{parts[0]} ({parts[1]}): {parts[2]}"

            else:
                return f"{parts[0]}: {parts[2]}"

        else:
            raise Exception(f"Too many parts in {val}")

    else:
        return val


def build_compose(docker_compose_file, filename, show_defaults=False):

    compose_yaml = None
    with open(docker_compose_file, "r") as f:
        compose_yaml = yaml.safe_load(f)

    if compose_yaml is None:
        raise Exception("Yaml not loaded.")

    services = {}

    node_attrs = {
        # "width": "1.3"
        "fixedsize": "false",
        "fontsize": "40",
        "labelfontsize": "40",
        # "labelfloat": "true",
        "margin": "2",
    }

    graph_attrs = {
        "voro_margin": "0.1",
        #   "layout": "neato",
        #    "fontsize": "100"
        "compound": "true",
        "labelloc": "b",
        "fontsize": "40",
        #    "root": "Local Services"
    }

    edge_attrs = {"fontsize": "40", "labelfontsize": "40", "labelfloat": "false"}

    with Diagram(
        os.path.basename(docker_compose_file),
        filename=filename,
        show=True,
        graph_attr=graph_attrs,
    ):

        service_clusters = {}
        volumes = {}

        # with Cluster("Local Services", graph_attr=graph_attrs):
        localhost = Server(xlabel="localhost", **node_attrs)

        # create mounted volumes
        for service_name, service_config in compose_yaml["services"].items():

            if "volumes" in service_config.keys():
                for volume in service_config["volumes"]:

                    storage = None

                    if isinstance(volume, (str,)):
                        volume = clean_mapped_value(volume, show_defaults=show_defaults)
                        storage = FileStorage(xlabel=volume, **node_attrs)

                    elif isinstance(volume, (dict,)):
                        volume_source = clean_mapped_value(
                            volume["source"], show_defaults=show_defaults
                        )
                        volume_target = clean_mapped_value(
                            volume["target"], show_defaults=show_defaults
                        )

                        storage = FileStorage(
                            xlabel=f"{volume_source}:{volume_target}", **node_attrs
                        )

                    if not volumes.get(service_name):
                        volumes[service_name] = [storage]

                    else:
                        volumes[service_name].append(storage)

        # create high-level service cluster
        with Cluster("LUME-services", graph_attr=graph_attrs):

            # create sub clusters... should only be one network
            for network in compose_yaml["networks"]:
                service_clusters[network] = Cluster(network, graph_attr=graph_attrs)

            for service_name, service_config in compose_yaml["services"].items():
                #  self.p(f"Service: {service_name}"

                if "networks" in service_config.keys():
                    # use first network for registering
                    network_name = service_config["networks"][0]
                    if network_name == "default":
                        container = Docker(service_name, **node_attrs)

                    else:
                        with service_clusters[network_name]:
                            container = Docker(service_name, **node_attrs)

                else:
                    container = Docker(service_name, **node_attrs)

                services[service_name] = container

                if volumes.get(service_name) is not None:
                    for volume in volumes.get(service_name):
                        container << volume

                if "ports" in service_config.keys():
                    for port in service_config["ports"]:
                        (
                            container
                            << Edge(
                                label=clean_mapped_value(
                                    port, show_defaults=show_defaults
                                ),
                                **edge_attrs,
                            )
                            << localhost
                        )

        # compose dependencies
        for service_name, service_config in compose_yaml["services"].items():
            # Dependency edges
            if "depends_on" in service_config.keys():
                for dep in service_config["depends_on"]:
                    # service_containers[service_name] << Edge(label=dep, color="red", style="dashed") << localhost
                    (
                        services[dep]
                        << Edge(color="red", style="dashed")
                        << services[service_name]
                    )


@click.command()
@click.option("--output_filename", required=True, type=str)
def build_compose_docs(output_filename):
    if ".png" in output_filename:
        output_filename = output_filename.replace(".png", "")
    build_compose(DOCKER_COMPOSE, output_filename)


@click.group()
def main():
    pass


main.add_command(build_compose_docs)


if __name__ == "__main__":
    main()
