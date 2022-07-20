::: lume_services.services.scheduling.backends.backend
    selection:
        filters:
            - "!^Config"
            - "!^_"  # exlude all members starting with _
            - "!^logger"


::: lume_services.services.scheduling.backends.local
    selection:
        filters:
            - "!^Config"
            - "!^_"  # exlude all members starting with _
            - "!^logger"


::: lume_services.services.scheduling.backends.server
    selection:
        filters:
            - "!^Config"
            - "!^_"  # exlude all members starting with _
            - "!^logger"


::: lume_services.services.scheduling.backends.docker
    selection:
        filters:
            - "!^Config"
            - "!^_"  # exlude all members starting with _
            - "!^logger"


::: lume_services.services.scheduling.backends.kubernetes
    selection:
        filters:
            - "!^Config"
            - "!^_"  # exlude all members starting with _
            - "!^logger"
