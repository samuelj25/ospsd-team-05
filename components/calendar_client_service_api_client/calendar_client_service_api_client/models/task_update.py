from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TaskUpdate")


@_attrs_define
class TaskUpdate:
    """Payload for updating an existing task.

    Attributes:
        id (str):
        title (str):
        end_time (datetime.datetime):
        description (None | str | Unset):
        is_completed (bool | Unset):  Default: False.
    """

    id: str
    title: str
    end_time: datetime.datetime
    description: None | str | Unset = UNSET
    is_completed: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        end_time = self.end_time.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_completed = self.is_completed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "end_time": end_time,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if is_completed is not UNSET:
            field_dict["is_completed"] = is_completed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        title = d.pop("title")

        end_time = isoparse(d.pop("end_time"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        is_completed = d.pop("is_completed", UNSET)

        task_update = cls(
            id=id,
            title=title,
            end_time=end_time,
            description=description,
            is_completed=is_completed,
        )

        task_update.additional_properties = d
        return task_update

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
