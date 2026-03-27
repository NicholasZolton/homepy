"""Tests for the Home class and base Resource interface."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyhomedot import Home
from pyhomedot.resources.base import Resource


class TestResource:
    """Test the base Resource abstract class."""

    def test_resource_is_abstract(self) -> None:
        """Cannot instantiate Resource directly."""
        with pytest.raises(TypeError):
            Resource()  # type: ignore[abstract]

    def test_resource_subclass_must_implement_generate(self) -> None:
        """Subclass without generate raises TypeError."""

        class BadResource(Resource):
            pass

        with pytest.raises(TypeError):
            BadResource()  # type: ignore[abstract]

    def test_resource_subclass_with_generate(self) -> None:
        """Subclass with generate can be instantiated."""

        class GoodResource(Resource):
            def generate(self, *, dry_run: bool = False) -> None:
                pass

        r = GoodResource()
        assert isinstance(r, Resource)


class TestHome:
    """Test the Home orchestrator."""

    def test_home_has_resources_list(self) -> None:
        home = Home()
        assert isinstance(home.resources, list)
        assert len(home.resources) == 0

    def test_home_generate_calls_all_resources(self) -> None:
        home = Home()
        r1 = MagicMock(spec=Resource)
        r2 = MagicMock(spec=Resource)
        home.resources.append(r1)
        home.resources.append(r2)
        home.generate()
        r1.generate.assert_called_once_with(dry_run=False, show_diff=False)
        r2.generate.assert_called_once_with(dry_run=False, show_diff=False)

    def test_home_generate_dry_run(self) -> None:
        home = Home()
        r1 = MagicMock(spec=Resource)
        home.resources.append(r1)
        home.generate(dry_run=True)
        r1.generate.assert_called_once_with(dry_run=True, show_diff=False)

    def test_home_generate_empty_resources(self) -> None:
        """Generate with no resources does nothing and doesn't error."""
        home = Home()
        home.generate()  # should not raise

    def test_home_add_resource(self) -> None:
        """Can add resources via add() method."""
        home = Home()
        r = MagicMock(spec=Resource)
        home.add(r)
        assert len(home.resources) == 1
        assert home.resources[0] is r

    def test_home_add_multiple_resources(self) -> None:
        """Can add multiple resources via add()."""
        home = Home()
        r1 = MagicMock(spec=Resource)
        r2 = MagicMock(spec=Resource)
        home.add(r1, r2)
        assert len(home.resources) == 2

    def test_home_add_returns_self(self) -> None:
        """add() returns self for chaining."""
        home = Home()
        r = MagicMock(spec=Resource)
        result = home.add(r)
        assert result is home
