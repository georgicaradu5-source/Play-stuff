import nox

# Reuse venvs to speed up local runs
nox.options.reuse_venv = "yes"


def _install_dev(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    # Minimal dev tools used by sessions
    session.install("pytest", "pytest-cov", "ruff", "mypy")


@nox.session
def lint(session: nox.Session) -> None:
    """Run Ruff lint checks."""
    _install_dev(session)
    session.run("ruff", "check", ".")


@nox.session
def type(session: nox.Session) -> None:  # noqa: A003 - intentional session name
    """Run mypy type checks for src."""
    _install_dev(session)
    session.run("mypy", "src")


@nox.session
def test(session: nox.Session) -> None:
    """Run unit tests with coverage and enforce >=10% (demo mode)."""
    _install_dev(session)
    session.run(
        "pytest",
        "-q",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-fail-under=10",
    )


@nox.session
def all(session: nox.Session) -> None:  # noqa: A003 - intentional session name
    """Run lint, type, and test sequentially."""
    session.log("Running lint → type → test")
    session.notify("lint")
    session.notify("type")
    session.notify("test")
