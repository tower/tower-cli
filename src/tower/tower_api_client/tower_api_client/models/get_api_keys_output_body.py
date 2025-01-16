from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="GetAPIKeysOutputBody")


@_attrs_define
class GetAPIKeysOutputBody:
    """
    Attributes:
        api_keys (Union[None, list['APIKey']]): List of API keys
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    api_keys: Union[None, list["APIKey"]]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        api_keys: Union[None, list[dict[str, Any]]]
        if isinstance(self.api_keys, list):
            api_keys = []
            for api_keys_type_0_item_data in self.api_keys:
                api_keys_type_0_item = api_keys_type_0_item_data.to_dict()
                api_keys.append(api_keys_type_0_item)

        else:
            api_keys = self.api_keys

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "api_keys": api_keys,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = src_dict.copy()

        def _parse_api_keys(data: object) -> Union[None, list["APIKey"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                api_keys_type_0 = []
                _api_keys_type_0 = data
                for api_keys_type_0_item_data in _api_keys_type_0:
                    api_keys_type_0_item = APIKey.from_dict(api_keys_type_0_item_data)

                    api_keys_type_0.append(api_keys_type_0_item)

                return api_keys_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["APIKey"]], data)

        api_keys = _parse_api_keys(d.pop("api_keys"))

        schema = d.pop("$schema", UNSET)

        get_api_keys_output_body = cls(
            api_keys=api_keys,
            schema=schema,
        )

        return get_api_keys_output_body
