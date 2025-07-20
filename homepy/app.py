from homepy import Home
from homepy.resources import SymlinkResource
from pathlib import Path
import typer
import asyncio

app = typer.Typer()


@app.command(name="generate")
def generate() -> None:
    """
    Generate the given home configuration.
    """
    print(f"Generating home from app directory {typer.get_app_dir('homepy')}")


@app.command(name="init")
def init() -> None:
    """
    Initialize a configuration directory.
    """
    print(f"Initializing configuration directory {typer.get_app_dir('homepy')}...")
    Path(typer.get_app_dir("homepy")).mkdir(parents=True, exist_ok=True)

    # generate a requirements.txt file that lets the user install homepy as a package
    requirements_path = Path(typer.get_app_dir("homepy")) / "requirements.txt"
    if not requirements_path.exists():
        with open(requirements_path, "w") as f:
            f.write("homepy")
            f.close()
    else:
        print("requirements.txt already exists, skipping")

    # write a main file that just does def main() etc. then home = Home()
    main_py_path = Path(typer.get_app_dir("homepy")) / "main.py"
    if not main_py_path.exists():
        with open(main_py_path, "w") as f:
            f.write("def main():\n\thome = Home()\n\n")
            f.close()
    else:
        print("main.py already exists, skipping")


if __name__ == "__main__":
    app()
