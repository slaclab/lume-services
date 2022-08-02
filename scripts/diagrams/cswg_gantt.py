from datetime import date
import gantt

# Change font default
gantt.define_font_attributes(
    fill="black", stroke="black", stroke_width=0, font_family="Verdana"
)


# Create a project
online_modeling_service = gantt.Project(name="Online Modeling Service")


lume_services = gantt.Project(name="LUME-services", color="#D9C5B2")

# lume-services projects
template = gantt.Task(
    name="Project Templating", start=date(2022, 8, 1), duration=14, percent_done=50
)
scheduling = gantt.Task(
    name="Scheduling Service", start=date(2022, 6, 20), duration=40, percent_done=90
)
dev = gantt.Task(
    name="Development Environment",
    start=date(2022, 6, 20),
    duration=40,
    percent_done=75,
)
modeling = gantt.Task(
    name="Modeling Interface", start=date(2022, 5, 15), duration=45, percent_done=75
)
results = gantt.Task(
    name="Results Interface", start=date(2022, 5, 15), duration=14, percent_done=100
)
files = gantt.Task(
    name="Files Interface", start=date(2022, 5, 1), duration=14, percent_done=100
)
release = gantt.Milestone(
    name="LUME-services v0.1.0",
    depends_of=[template, modeling, results, files, scheduling],
)

for project in [template, modeling, results, files, scheduling, release, dev]:
    lume_services.add_task(project)

online_modeling_service.add_task(lume_services)


# slac-services
slac_services = gantt.Project(name="SLAC-services", color="#7FD1B9")
slurm = gantt.Task(
    name="Slurm Interface", start=date(2022, 9, 1), duration=7, percent_done=0
)
snapshot_routine = gantt.Task(
    name="Synchronous Snapshot Routine",
    start=date(2022, 9, 1),
    duration=15,
    percent_done=0,
)

slac_services.add_task(snapshot_routine)
slac_services.add_task(slurm)

online_modeling_service.add_task(slac_services)

# output service
output_service = gantt.Project(name="Output IOC", color="#a3ddcb")
lume_epics_server = gantt.Task(
    name="LUME-EPICS output-only server",
    start=date(2022, 9, 1),
    duration=15,
    percent_done=25,
)
# output_service.add_task(lume_epics_server)
containerized_ioc = gantt.Task(
    name="Containerized IOC", duration=7, percent_done=50, depends_of=lume_epics_server
)
# output_service.add_task(containerized_ioc)
for task in [lume_epics_server, containerized_ioc]:
    output_service.add_task(task)

online_modeling_service.add_task(output_service)

# kubernetes deployment
kubernetes_deployment = gantt.Project(name="Kubernetes Deployment", color="#B0BEA9")
model_db = gantt.Task(
    name="MySQL Operator (model db)",
    start=date(2022, 6, 1),
    duration=14,
    percent_done=75,
    depends_of=release,
)
results_db = gantt.Task(
    name="Mongodb Operator (results db)",
    start=date(2022, 6, 1),
    duration=14,
    percent_done=75,
    depends_of=release,
)
prefect = gantt.Task(
    name="Prefect Server",
    start=date(2022, 6, 1),
    duration=15,
    percent_done=75,
    depends_of=release,
)
synchronous_snapshot = gantt.Task(
    name="Synchronous Snapshot Service",
    start=date(2022, 8, 15),
    duration=7,
    percent_done=0,
    depends_of=snapshot_routine,
)
output = gantt.Task(
    name="Output IOC Service",
    start=date(2022, 9, 16),
    duration=14,
    percent_done=25,
    depends_of=containerized_ioc,
)

kubernetes_deployment.add_task(model_db)
for task in [results_db, prefect, synchronous_snapshot, output]:
    kubernetes_deployment.add_task(task)

online_modeling_service.add_task(kubernetes_deployment)

deployments = gantt.Project(name="Milestone Model Deployments")
deployment_of_impact_model = gantt.Task(
    "Impact-T cu_inj",
    duration=14,
    percent_done=50,
    depends_of=[template, kubernetes_deployment, output_service, synchronous_snapshot],
)
deployment_of_bmad_model = gantt.Task(
    "Bmad cu_ beamlines",
    duration=14,
    percent_done=50,
    depends_of=[template, kubernetes_deployment, output_service, synchronous_snapshot],
)
deployment_of_surrogate = gantt.Task(
    "ML surrogate for Impact-T cu_inj",
    duration=14,
    percent_done=50,
    depends_of=[template, kubernetes_deployment, output_service, synchronous_snapshot],
)


for task in [
    deployment_of_bmad_model,
    deployment_of_impact_model,
    deployment_of_surrogate,
]:
    deployments.add_task(task)

online_modeling_service.add_task(deployments)

online_modeling_service.make_svg_for_tasks(
    filename="OMS.svg",
    today=date(2022, 7, 25),
    start=date(2022, 5, 1),
    end=date(2022, 11, 14),
    scale=gantt.DRAW_WITH_WEEKLY_SCALE,
)
