from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunnerCredentials")


@_attrs_define
class RunnerCredentials:
    """
    Attributes:
        certificate (str): The signed certificate used by the runner to authenticate itself to Tower.
        private_key (str): The private key used by the runner to authenticate itself to Tower.
        root_ca (Union[None, str]): The PEM encoded root CA certificate that is used to verify the runner's certificate
            when Tower is responsible for signing server certs.
        runner_service_url (str): The host of the runner service that this runner will connect to. This is typically the
            Tower service host.
    """

    certificate: str
    private_key: str
    root_ca: Union[None, str]
    runner_service_url: str

    def to_dict(self) -> dict[str, Any]:
        certificate = self.certificate

        private_key = self.private_key

        root_ca: Union[None, str]
        root_ca = self.root_ca

        runner_service_url = self.runner_service_url

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "certificate": certificate,
                "private_key": private_key,
                "root_ca": root_ca,
                "runner_service_url": runner_service_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        certificate = d.pop("certificate")

        private_key = d.pop("private_key")

        def _parse_root_ca(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        root_ca = _parse_root_ca(d.pop("root_ca"))

        runner_service_url = d.pop("runner_service_url")

        runner_credentials = cls(
            certificate=certificate,
            private_key=private_key,
            root_ca=root_ca,
            runner_service_url=runner_service_url,
        )

        return runner_credentials
