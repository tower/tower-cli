from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_detail import ErrorDetail


T = TypeVar("T", bound="ErrorModel")


@_attrs_define
class ErrorModel:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ErrorModel.json.
        detail (Union[Unset, str]): A human-readable explanation specific to this occurrence of the problem. Example:
            Property foo is required but is missing..
        errors (Union[Unset, list['ErrorDetail']]): Optional list of individual error details
        instance (Union[Unset, str]): A URI reference that identifies the specific occurrence of the problem. Example:
            https://example.com/error-log/abc123.
        status (Union[Unset, int]): HTTP status code Example: 400.
        title (Union[Unset, str]): A short, human-readable summary of the problem type. This value should not change
            between occurrences of the error. Example: Bad Request.
        type_ (Union[Unset, str]): A URI reference to human-readable documentation for the error. Default:
            'about:blank'. Example: https://example.com/errors/example.
    """

    schema: Union[Unset, str] = UNSET
    detail: Union[Unset, str] = UNSET
    errors: Union[Unset, list["ErrorDetail"]] = UNSET
    instance: Union[Unset, str] = UNSET
    status: Union[Unset, int] = UNSET
    title: Union[Unset, str] = UNSET
    type_: Union[Unset, str] = "about:blank"

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        detail = self.detail

        errors: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.errors, Unset):
            errors = []
            for errors_item_data in self.errors:
                errors_item = errors_item_data.to_dict()
                errors.append(errors_item)

        instance = self.instance

        status = self.status

        title = self.title

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if detail is not UNSET:
            field_dict["detail"] = detail
        if errors is not UNSET:
            field_dict["errors"] = errors
        if instance is not UNSET:
            field_dict["instance"] = instance
        if status is not UNSET:
            field_dict["status"] = status
        if title is not UNSET:
            field_dict["title"] = title
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail

        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        detail = d.pop("detail", UNSET)

        errors = []
        _errors = d.pop("errors", UNSET)
        for errors_item_data in _errors or []:
            errors_item = ErrorDetail.from_dict(errors_item_data)

            errors.append(errors_item)

        instance = d.pop("instance", UNSET)

        status = d.pop("status", UNSET)

        title = d.pop("title", UNSET)

        type_ = d.pop("type", UNSET)

        error_model = cls(
            schema=schema,
            detail=detail,
            errors=errors,
            instance=instance,
            status=status,
            title=title,
            type_=type_,
        )

        return error_model
