from diagrams import Cluster, Diagram
from diagrams.custom import Custom
from diagrams.k8s.storage import Volume
from diagrams.k8s.compute import Pod
from diagrams.onprem.database import Mongodb, Mysql
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage

# ? marks should check in on org

with Diagram("Kubernetes Architecture", show=True):
    with Cluster("K8s"):
        with Cluster("Prefect Service Cluster"):
            apollo = Pod("apollo")
            graphql = Pod("graphql")
            hasura = Pod("hasura")
            postgres = Pod("postgres")
            prefect_services = [apollo, graphql, hasura, postgres]

        agent = Pod("Prefect Agent")

        with Cluster("Model Execution Jobs"):
            jobs = [Pod("Model Run"), Pod("Model Run")]

    user = Python("User")
    #  with Cluster("Logging Stack"):
    #      logging =  [Pod("Loki"), Pod("Grafana")]

    with Cluster("Resources"):
        results_db = Mongodb("Results Database")
        model_db = Mysql("Model Database")

    stanford_container_registry = Storage("Stanford Container Registry")

    user >> model_db
    user << model_db
    user >> apollo
    apollo >> agent >> jobs
    jobs >> results_db
    # user << results_db
    agent << stanford_container_registry
    user >> stanford_container_registry

    # queue = Custom("Message queue", rabbitmq_icon)

#  queue >> consumers >> Aurora("Database")
