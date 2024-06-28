import nox


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"], tags=["test"])
def test(session: nox.Session) -> None:
    session.install(".", ".[dev]")
    session.run("pytest", "-n", "4")
