from __future__ import annotations

import re
from typing import AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.licenses import Licenses

# https://data.norge.no/nb/datasets/af15237b-c5d7-421d-bb29-ca05f3c458ff/nasjonalt-barnehageregister-nbr


class NbrBarnehageregisterNOSpider(Spider):
    name = "nbr_barnehageregister_no"
    allowed_domains = ["data-nbr.udir.no"]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Utdanningsdirektoratet"
    }
    api_base_url = "https://data-nbr.udir.no"
    page_size = 1000

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"{self.api_base_url}/v4/enheter?sidenummer=1&antallperside={self.page_size}",
            callback=self.get_pages,
        )

    def get_pages(self, response: TextResponse) -> Iterable[JsonRequest]:
        """Yield all page requests upfront for parallel execution."""
        payload = response.json()
        total_pages = payload.get("AntallSider", 1)

        for page in range(1, total_pages + 1):
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

            # Only fetch details for active kindergartens.
            if enhet.get("ErAktiv") is not True:
                continue

            # Filter out non-kindergarten entities.
            if enhet.get("ErBarnehage") is not True:
                continue

            # Fetch detailed information for each entity.
            yield JsonRequest(
                url=f"{self.api_base_url}/v4/enhet/{orgnr}",
                callback=self.parse_enhet,
                cb_kwargs={"summary": enhet},
            )

    def parse_enhet(self, response: TextResponse, summary: dict) -> Iterable[Feature]:
        data = response.json()

        # Exclude excluded kindergartens.
        if data.get("ErEkskludert") is True:
            return

        # If entity somehow is inactive or not a kindergarten after filtering, exclude it.
        if data.get("ErAktiv") is not True or data.get("ErBarnehage") is not True:
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

        # Operator type
        if data.get("ErOffentligBarnehage") is True:
            item["extras"]["operator:type"] = "government"
        elif data.get("ErPrivatBarnehage") is True:
            item["extras"]["operator:type"] = "private"

        # ISCED level 0: early childhood education.
        item["extras"]["isced:level"] = "0"

        # Age range
        if (min_age := data.get("AlderstrinnFra")) is not None:
            item["extras"]["min_age"] = str(min_age)
        if (max_age := data.get("AlderstrinnTil")) is not None:
            item["extras"]["max_age"] = str(max_age)

        # Capacity
        if (antall_barn := data.get("AntallBarn")) not in (None, 0):
            item["extras"]["capacity"] = antall_barn

        # Category
        apply_category(Categories.KINDERGARTEN, item)

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
