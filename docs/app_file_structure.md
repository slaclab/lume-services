

```

Online-Modeling-Service/
├─ models/
|  ├─ images/
|  |  ├─ generic_base.tar
│  │  ├─ my_model_v0.1.tar
├─ services/
|  ├─ data/
|  |  ├─ epics/
|  |  |  ├─ ds/
|  |  |  ├─ log/
|  │  ├─ elasticsearch/
|  │  ├─ mysql/
|  │  ├─ mongodb/
|  ├─ charts/
|  │  ├─ elg/
|  |  |  ├─ Chart.yaml
|  |  |  ├─ values.yaml
|  │  ├─ results_db/
|  |  |  ├─ values.yaml
|  │  ├─ model_db/
|  |  |  ├─ values.yaml
|  │  ├─ prefect/
|  |  |  ├─ values.yaml
|  |  ├─ sync_snapshot/
|  |  |  ├─ Chart.yaml
|  |  |  ├─ values.yaml
|  |  ├─ epics_output/
|  |  |  ├─ Chart.yaml
|  |  |  ├─ values.yaml
|  │  ├─ umbrella_chart.yaml


```



```yaml

"{{cookiecutter.repo_name}}"
├─ .github/
|  ├─ workflows/
|  |  ├─ build_flow_docker.yaml
│  │  ├─ tests.yaml
├─ "{{cookiecutter.project_slug}}"
|  ├─ files/
|  |  ├─ __init__.py
|  |  ├─ variables.yaml
|  ├─ flow/
|  |  ├─ __init__.py
|  |  ├─ _entrypoint.sh
|  |  ├─ Dockerfile
|  |  ├─ flow.py
|  ├─ tests/
|  ├─ __init__.py
|  ├─ config.py
|  ├─ model.py
├─ dev-requirements.txt
├─ requirements.txt
├─ README.md
├─ MANIFEST.in
├─ setup.cfg
├─ setup.py
├─ model.yaml

```

