from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateUserParams")


@_attrs_define
class UpdateUserParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateUserParams.json.
        company (None | str | Unset):
        country (None | str | Unset):
        first_name (None | str | Unset):
        is_alerts_enabled (bool | None | Unset):
        is_subscribed_to_changelog (bool | None | Unset): If true, the user will receive changelog updates via email.
        is_subscribed_to_marketing_emails (bool | None | Unset): If true, the user will receive marketing emails from
            Tower.
        is_subscribed_to_newsletter (bool | None | Unset): If true, the user will receive the Tower newsletter.
        last_name (None | str | Unset):
        password (None | str | Unset):
        promo_code (None | str | Unset):
    """

    schema: str | Unset = UNSET
    company: None | str | Unset = UNSET
    country: None | str | Unset = UNSET
    first_name: None | str | Unset = UNSET
    is_alerts_enabled: bool | None | Unset = UNSET
    is_subscribed_to_changelog: bool | None | Unset = UNSET
    is_subscribed_to_marketing_emails: bool | None | Unset = UNSET
    is_subscribed_to_newsletter: bool | None | Unset = UNSET
    last_name: None | str | Unset = UNSET
    password: None | str | Unset = UNSET
    promo_code: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        company: None | str | Unset
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        country: None | str | Unset
        if isinstance(self.country, Unset):
            country = UNSET
        else:
            country = self.country

        first_name: None | str | Unset
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        is_alerts_enabled: bool | None | Unset
        if isinstance(self.is_alerts_enabled, Unset):
            is_alerts_enabled = UNSET
        else:
            is_alerts_enabled = self.is_alerts_enabled

        is_subscribed_to_changelog: bool | None | Unset
        if isinstance(self.is_subscribed_to_changelog, Unset):
            is_subscribed_to_changelog = UNSET
        else:
            is_subscribed_to_changelog = self.is_subscribed_to_changelog

        is_subscribed_to_marketing_emails: bool | None | Unset
        if isinstance(self.is_subscribed_to_marketing_emails, Unset):
            is_subscribed_to_marketing_emails = UNSET
        else:
            is_subscribed_to_marketing_emails = self.is_subscribed_to_marketing_emails

        is_subscribed_to_newsletter: bool | None | Unset
        if isinstance(self.is_subscribed_to_newsletter, Unset):
            is_subscribed_to_newsletter = UNSET
        else:
            is_subscribed_to_newsletter = self.is_subscribed_to_newsletter

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        password: None | str | Unset
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        promo_code: None | str | Unset
        if isinstance(self.promo_code, Unset):
            promo_code = UNSET
        else:
            promo_code = self.promo_code

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if company is not UNSET:
            field_dict["company"] = company
        if country is not UNSET:
            field_dict["country"] = country
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if is_alerts_enabled is not UNSET:
            field_dict["is_alerts_enabled"] = is_alerts_enabled
        if is_subscribed_to_changelog is not UNSET:
            field_dict["is_subscribed_to_changelog"] = is_subscribed_to_changelog
        if is_subscribed_to_marketing_emails is not UNSET:
            field_dict["is_subscribed_to_marketing_emails"] = (
                is_subscribed_to_marketing_emails
            )
        if is_subscribed_to_newsletter is not UNSET:
            field_dict["is_subscribed_to_newsletter"] = is_subscribed_to_newsletter
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if password is not UNSET:
            field_dict["password"] = password
        if promo_code is not UNSET:
            field_dict["promo_code"] = promo_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        def _parse_company(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_country(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        country = _parse_country(d.pop("country", UNSET))

        def _parse_first_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_is_alerts_enabled(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_alerts_enabled = _parse_is_alerts_enabled(d.pop("is_alerts_enabled", UNSET))

        def _parse_is_subscribed_to_changelog(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_subscribed_to_changelog = _parse_is_subscribed_to_changelog(
            d.pop("is_subscribed_to_changelog", UNSET)
        )

        def _parse_is_subscribed_to_marketing_emails(
            data: object,
        ) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_subscribed_to_marketing_emails = _parse_is_subscribed_to_marketing_emails(
            d.pop("is_subscribed_to_marketing_emails", UNSET)
        )

        def _parse_is_subscribed_to_newsletter(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_subscribed_to_newsletter = _parse_is_subscribed_to_newsletter(
            d.pop("is_subscribed_to_newsletter", UNSET)
        )

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_promo_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        promo_code = _parse_promo_code(d.pop("promo_code", UNSET))

        update_user_params = cls(
            schema=schema,
            company=company,
            country=country,
            first_name=first_name,
            is_alerts_enabled=is_alerts_enabled,
            is_subscribed_to_changelog=is_subscribed_to_changelog,
            is_subscribed_to_marketing_emails=is_subscribed_to_marketing_emails,
            is_subscribed_to_newsletter=is_subscribed_to_newsletter,
            last_name=last_name,
            password=password,
            promo_code=promo_code,
        )

        return update_user_params
