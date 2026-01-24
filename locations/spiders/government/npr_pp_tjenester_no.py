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

# https://data.norge.no/data-services/6cb2bcbf-a24b-32e7-bd18-a8e83353fdde


class NprPPTjenesterNOSpider(Spider):
    name = "npr_pp_tjenester_no"
    allowed_domains = ["data-npr.udir.no"]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Utdanningsdirektoratet"
    }
    api_base_url = "https://data-npr.udir.no"
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

            # Only fetch details for active PP Tjeneste.
            if enhet.get("ErAktiv") is not True:
                continue

            # Filter out non-PP Tjenester.
            if enhet.get("ErPPtjeneste") is not True:
                continue

            # Fetch detailed information for each entity.
            yield JsonRequest(
                url=f"{self.api_base_url}/v4/enhet/{orgnr}",
                callback=self.parse_enhet,
                cb_kwargs={"summary": enhet},
            )

    def parse_enhet(self, response: TextResponse, summary: dict) -> Iterable[Feature]:
        data = response.json()

        if data.get("ErEkskludert") is True:
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

        # Number of employees
        if (ansatte := data.get("AntallAnsatte")) not in (None, 0):
            item["extras"]["employees"] = ansatte

        # Operator information from ForeldreRelasjoner
        # See: https://data-npr.udir.no/v4/relasjonstyper
        for relasjon in data.get("ForeldreRelasjoner") or []:
            relasjonstype = relasjon.get("Relasjonstype") or {}
            # 41 (Eierstruktur) = ownership structure, i.e. who owns/operates the entity
            if relasjonstype.get("Id") == "41":
                if enhet := relasjon.get("Enhet"):
                    if navn := enhet.get("Navn"):
                        item["operator"] = navn
                break

        # Category: PP-tjenesten is a municipal/county government educational-psychological service
        # that supports schools and kindergartens with special education needs assessment
        apply_category({"office": "government", "government": "education"}, item)

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
