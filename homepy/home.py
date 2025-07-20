from abc import abstractmethod
from typing import List
from rich.progress import track


class HomeResource:
    @abstractmethod
    def generate(self, verbose: bool = False) -> None:
        """Generate the resource."""


class Home:
    """
    Represents a home configuration.
    """

    def __init__(self) -> None:
        self.resources: List[HomeResource] = []

    def generate(self, verbose: bool = False) -> None:
        """Generate all configured resources."""
        for resource in track(
            self.resources, description="Generating home resources..."
        ):
            resource.generate(verbose=verbose)
        print("Home generated!")
