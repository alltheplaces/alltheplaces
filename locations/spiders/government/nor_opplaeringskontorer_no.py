from __future__ import annotations

import re
from typing import AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.licenses import Licenses

# https://data.norge.no/data-services/325d8445-6868-3986-afd5-bb58ae34dd01


class NorOpplaeringskontorerNOSpider(Spider):
    name = "nor_opplaeringskontorer_no"
    allowed_domains = ["data-nor.udir.no"]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Utdanningsdirektoratet"
    }
    api_base_url = "https://data-nor.udir.no"
    page_size = 1000

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"{self.api_base_url}/v4/enheter?sidenummer=1&antallperside={self.page_size}",
            callback=self.get_pages,
        )

    def get_pages(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        payload = response.json()
        total_pages = payload.get("AntallSider", 1)

        yield from self.parse(response)

        for page in range(2, total_pages + 1):
            yield JsonRequest(
                url=f"{self.api_base_url}/v4/enheter?sidenummer={page}&antallperside={self.page_size}",
            )

    def parse(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        payload = response.json()

        for enhet in payload.get("EnhetListe") or []:
            # Ensure we have an organization number.
            orgnr = enhet.get("Organisasjonsnummer")
            if not orgnr:
                continue

            # Only fetch details for active Apprenticeship Office.
            if enhet.get("ErAktiv") is not True:
                continue

            # Filter out non-apprenticeship Office.
            if enhet.get("ErOpplaeringskontor") is not True:
                continue

            # Fetch detailed information for each entity.
            yield JsonRequest(
                url=f"{self.api_base_url}/v4/enhet/{orgnr}",
                callback=self.parse_enhet,
                cb_kwargs={"summary": enhet},
            )

    def parse_enhet(self, response: TextResponse, summary: dict) -> Iterable[Feature]:
        data = response.json()

        # If entity somehow is inactive or not a Apprenticeship Office after filtering, exclude it.
        if data.get("ErAktiv") is not True or data.get("ErOpplaeringskontor") is not True:
            return

        item = DictParser.parse(data)
        item["ref"] = data.get("Organisasjonsnummer") or summary.get("Organisasjonsnummer")

        # Website
        if website := normalize_website(item.get("website")):
            item["website"] = website
        else:
            item.pop("website", None)

        # Location
        if postadresse := data.get("Postadresse"):
            item["street_address"] = postadresse.get("Adresse")
        if fylke := data.get("Fylke"):
            item["state"] = fylke.get("Navn")

        # Number of apprentices if available
        if (antall_laerlinger := data.get("AntallLaerlinger")) not in (None, 0):
            item["extras"]["capacity"] = str(antall_laerlinger)
        if (ansatte := data.get("AntallAnsatte")) not in (None, 0):
            item["extras"]["employees"] = ansatte

        # Operator information from ForeldreRelasjoner
        # See: https://data-nor.udir.no/v4/relasjonstyper
        for relasjon in data.get("ForeldreRelasjoner") or []:
            relasjonstype = relasjon.get("Relasjonstype") or {}
            # 22 (Eierstruktur) = ownership structure, i.e. who owns/operates the entity
            if relasjonstype.get("Id") == "22":
                if enhet := relasjon.get("Enhet"):
                    if navn := enhet.get("Navn"):
                        item["operator"] = navn
                break

        # Operator type based on Organisasjonsform
        # See: https://data-nor.udir.no/v4/organisasjonsformer
        if organisasjonsform := data.get("Organisasjonsform"):
            org_id = organisasjonsform.get("Id")
            if org_id in ("KOMM", "FYLK", "STAT"):
                item["extras"]["operator:type"] = "government"
            elif org_id in ("ADOS", "FKF", "KF", "SF", "IKS"):
                item["extras"]["operator:type"] = "public"
            elif org_id == "KIRK":
                item["extras"]["operator:type"] = "religious"
            elif org_id in ("SA", "BBL", "BRL", "GFS"):
                item["extras"]["operator:type"] = "cooperative"
            elif org_id in ("FLI", "ORGL", "STI"):
                item["extras"]["operator:type"] = "association"
            elif org_id in ("AS", "ASA", "BA", "ENK", "DA", "ANS", "KS", "NUF", "SE", "PRE"):
                item["extras"]["operator:type"] = "private"

        # Category: training office
        apply_category({"office": "educational_institution", "education": "training"}, item)

        yield item


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)

        # Check against check_item_properties.py URL regex
        url_regex = re.compile(
            r"^(?:http)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
            r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        return all([result.scheme, result.netloc]) and url_regex.match(url) is not None
    except ValueError:
        return False


def normalize_website(raw: str | None) -> str | None:
    if not raw:
        return None

    website = raw.strip()
    if not website:
        return None

    if not website.startswith(("http://", "https://")):
        website = "https://" + website.lstrip("/")

    if not is_valid_url(website):
        return None

    return website
