"""Example usage of pyhomedot."""

from __future__ import annotations

import os

from pyhomedot import Home
from pyhomedot.resources import SymlinkResource, PackageResource


def main() -> None:
    home = Home()

    resources: list[SymlinkResource | PackageResource] = [
        SymlinkResource("files/home/hello.txt", "hello.txt", force=True),
        SymlinkResource("files/git/", ".config/git/", force=True),
    ]

    if os.uname().sysname == "Darwin":
        resources.append(PackageResource("htop", "brew"))
    elif os.uname().sysname == "Linux":
        resources.append(PackageResource("htop", "apt"))

    for resource in resources:
        home.resources.append(resource)

    home.generate()


if __name__ == "__main__":
    main()
