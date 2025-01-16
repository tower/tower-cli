from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_detail import ErrorDetail


T = TypeVar("T", bound="ErrorModel")


@_attrs_define
class ErrorModel:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
        detail (Union[Unset, str]): A human-readable explanation specific to this occurrence of the problem.
        errors (Union[None, Unset, list['ErrorDetail']]): Optional list of individual error details
        instance (Union[Unset, str]): A URI reference that identifies the specific occurrence of the problem.
        status (Union[Unset, int]): HTTP status code
        title (Union[Unset, str]): A short, human-readable summary of the problem type. This value should not change
            between occurrences of the error.
        type_ (Union[Unset, str]): A URI reference to human-readable documentation for the error. Default:
            'about:blank'.
    """

    schema: Union[Unset, str] = UNSET
    detail: Union[Unset, str] = UNSET
    errors: Union[None, Unset, list["ErrorDetail"]] = UNSET
    instance: Union[Unset, str] = UNSET
    status: Union[Unset, int] = UNSET
    title: Union[Unset, str] = UNSET
    type_: Union[Unset, str] = "about:blank"

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        detail = self.detail

        errors: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.errors, Unset):
            errors = UNSET
        elif isinstance(self.errors, list):
            errors = []
            for errors_type_0_item_data in self.errors:
                errors_type_0_item = errors_type_0_item_data.to_dict()
                errors.append(errors_type_0_item)

        else:
            errors = self.errors

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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail

        d = src_dict.copy()
        schema = d.pop("$schema", UNSET)

        detail = d.pop("detail", UNSET)

        def _parse_errors(data: object) -> Union[None, Unset, list["ErrorDetail"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                errors_type_0 = []
                _errors_type_0 = data
                for errors_type_0_item_data in _errors_type_0:
                    errors_type_0_item = ErrorDetail.from_dict(errors_type_0_item_data)

                    errors_type_0.append(errors_type_0_item)

                return errors_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["ErrorDetail"]], data)

        errors = _parse_errors(d.pop("errors", UNSET))

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
