"""The pipeline interface.

A pipeline receives an already-open reader, a resolved configuration and an
execution context. File opening, backend selection and metadata resolution all
happen in :mod:`holodoppler.execution.runner`, so a pipeline does numerical work
and output writing only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Mapping

from holodoppler.readers import FileReader


if TYPE_CHECKING:  # pragma: no cover - typing only
    from holodoppler.execution.context import ExecutionContext


class Pipeline(ABC):
    """A named processing pipeline.

    Attributes
    ----------
    name:
        The name the pipeline is registered under. Set by each subclass and
        declared in :mod:`holodoppler.pipelines.registry`.
    """

    name: ClassVar[str] = ""

    @abstractmethod
    def process(
        self,
        file: FileReader,
        config: Mapping[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Process the whole input.

        Returns
        -------
        Any
            The primary numerical result, or ``None``. Pipelines currently
            write their own outputs via :mod:`holodoppler.saving`.
        """

    def preview(
        self,
        file: FileReader,
        config: Mapping[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Process a single reference batch.

        Raises
        ------
        NotImplementedError
            When the pipeline has no preview implementation. Check
            :meth:`supports_preview` first.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement preview()"
        )

    @classmethod
    def supports_preview(cls) -> bool:
        """Whether this pipeline implements :meth:`preview`."""
        return cls.preview is not Pipeline.preview

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
