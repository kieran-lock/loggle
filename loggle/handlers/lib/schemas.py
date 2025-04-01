from __future__ import annotations

from pathlib import Path
from logging import Formatter, Handler
from typing import Literal

from pydantic import ConfigDict, Field, field_serializer, field_validator, ValidationError, BaseModel, computed_field
from pydantic.alias_generators import to_camel

from ...formatters.lib.consts import BaseFormatterName
from .consts import BasePrimaryHandlerName, BasePrimaryHandlerName, LoggingStream
from ...lib.consts import LoggingLevel
from ...filters import BaseFilterName


class HandlerModel[T: BaseFilterName](BaseModel):
    handler_class: type[Handler] = Field(alias="class", serialization_alias="class")
    filters: list[T] | None = None


    @field_serializer("handler_class")
    def serialize_handler(self, handler_class: type[Handler]) -> str:
        return f"{handler_class.__module__}.{handler_class.__name__}"
    
    @field_validator("handler_class", mode="before")
    @classmethod
    def resolve_handler_class(cls, value: object) -> type[Handler]:
        if value is None:
            return Formatter
        if isinstance(value, type) and issubclass(value, Handler):
            return value
        if not isinstance(value, str):
            raise ValidationError("Field 'class' must be given a string or None.")
        parts = value.split(".")
        module = parts.pop(0)
        found = __import__(module)
        for part in parts:
            module = f"{module}.{part}"
            try:
                found = getattr(found, part)
            except AttributeError:
                __import__(module)
                found = getattr(found, part)
        return found
    
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class StreamHandlerSchema[T_FilterName: BaseFilterName, T_FormatterName: BaseFormatterName](HandlerModel[T_FilterName]):
    formatter: T_FormatterName
    level: LoggingLevel
    stream: LoggingStream


class FileHandlerSchema[T_FilterName: BaseFilterName, T_FormatterName: BaseFormatterName](HandlerModel[T_FilterName]):
    formatter: T_FormatterName
    level: LoggingLevel
    file_name: Path | None = Field(alias="filename", serialization_alias="filename", default=None)
    max_bytes: int
    backup_count: int
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class QueueHandlerSchema[T_PHandlerName: BasePrimaryHandlerName, T_FilterName: BaseFormatterName](HandlerModel[T_FilterName]):
    handlers: list[T_PHandlerName]
    respect_handler_level: bool = True

    @computed_field
    @property
    def _is_dictionary_configuration(self) -> Literal[True]:
        return True
