from diagrams import Cluster, Diagram
from diagrams.aws.database import Aurora
from diagrams.custom import Custom
from diagrams.k8s.compute import Pod

with Diagram("Broker Consumers", show=False):
    with Cluster("Consumers"):
        consumers = [Pod("worker"), Pod("worker"), Pod("worker")]

    # queue = Custom("Message queue", rabbitmq_icon)

    queue >> consumers >> Aurora("Database")
