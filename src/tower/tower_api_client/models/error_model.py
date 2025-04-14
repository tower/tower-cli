from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_detail import ErrorDetail


T = TypeVar("T", bound="ErrorModel")


@attr.s(auto_attribs=True)
class ErrorModel:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ErrorModel.json.
        detail (Union[Unset, str]): A human-readable explanation specific to this occurrence of the problem. Example:
            Property foo is required but is missing..
        errors (Union[Unset, List['ErrorDetail']]): Optional list of individual error details
        instance (Union[Unset, str]): A URI reference that identifies the specific occurrence of the problem. Example:
            https://example.com/error-log/abc123.
        status (Union[Unset, int]): HTTP status code Example: 400.
        title (Union[Unset, str]): A short, human-readable summary of the problem type. This value should not change
            between occurrences of the error. Example: Bad Request.
        type (Union[Unset, str]): A URI reference to human-readable documentation for the error. Default: 'about:blank'.
            Example: https://example.com/errors/example.
    """

    schema: Union[Unset, str] = UNSET
    detail: Union[Unset, str] = UNSET
    errors: Union[Unset, List["ErrorDetail"]] = UNSET
    instance: Union[Unset, str] = UNSET
    status: Union[Unset, int] = UNSET
    title: Union[Unset, str] = UNSET
    type: Union[Unset, str] = "about:blank"

    def to_dict(self) -> Dict[str, Any]:
        schema = self.schema
        detail = self.detail
        errors: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.errors, Unset):
            errors = []
            for errors_item_data in self.errors:
                errors_item = errors_item_data.to_dict()

                errors.append(errors_item)

        instance = self.instance
        status = self.status
        title = self.title
        type = self.type

        field_dict: Dict[str, Any] = {}
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
        if type is not UNSET:
            field_dict["type"] = type

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail

        d = src_dict.copy()
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

        type = d.pop("type", UNSET)

        error_model = cls(
            schema=schema,
            detail=detail,
            errors=errors,
            instance=instance,
            status=status,
            title=title,
            type=type,
        )

        return error_model
