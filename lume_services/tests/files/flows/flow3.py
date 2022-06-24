from prefect import task, Flow, Parameter


@task
def check_text_equivalence(text1, text2):
    assert text1 == text2


with Flow("flow3") as flow3:
    text1 = Parameter("text1")
    text2 = Parameter("text2")

    check_text_equivalence(text1, text2)
