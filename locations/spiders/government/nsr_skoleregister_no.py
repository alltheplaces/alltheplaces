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

# https://data.norge.no/nb/datasets/d8431635-2ae6-40af-b0ec-8869a2fa3f89/nasjonalt-skoleregister-nsr


class NsrSkoleregisterNOSpider(Spider):
    name = "nsr_skoleregister_no"
    allowed_domains = ["data-nsr.udir.no"]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Utdanningsdirektoratet"
    }

    api_base_url = "https://data-nsr.udir.no"
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

            if not is_valid_school(enhet):
                continue

            yield JsonRequest(
                url=f"{self.api_base_url}/v4/enhet/{orgnr}",
                callback=self.parse_enhet,
                cb_kwargs={"summary": enhet},
            )

    def parse_enhet(self, response: TextResponse, summary: dict) -> Iterable[Feature]:
        data = response.json()

        if not is_valid_school(data):
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
        if data.get("ErOffentligSkole") is True:
            item["extras"]["operator:type"] = "government"
        elif data.get("ErPrivatskole") is True:
            item["extras"]["operator:type"] = "private"

        # Grades
        self.derive_grades(item, data)

        # Special education needs
        if data.get("ErSpesialskole") is True:
            item["extras"]["school"] = "special_education_needs"

        # Capacity / staff
        if (elevtall := data.get("Elevtall")) not in (None, 0):
            item["extras"]["students"] = elevtall
        if (ansatte := data.get("AntallAnsatte")) not in (None, 0):
            item["extras"]["employees"] = ansatte

        apply_category(Categories.SCHOOL, item)

        yield item

    def derive_grades(self, item: Feature, data: dict) -> None:
        gs_from = data.get("SkoletrinnGSFra")
        gs_to = data.get("SkoletrinnGSTil")
        vgs_from = data.get("SkoletrinnVGSFra")
        vgs_to = data.get("SkoletrinnVGSTil")

        grades: list[str] = []
        if isinstance(gs_from, int) and isinstance(gs_to, int):
            grades.append(f"{gs_from}-{gs_to}")
        if isinstance(vgs_from, int) and isinstance(vgs_to, int):
            grades.append(f"{vgs_from}-{vgs_to}")

        if grades:
            item["extras"]["grades"] = ";".join(grades)


def is_valid_school(data: dict) -> bool:
    if data.get("ErEkskludert") or not data.get("ErAktiv") or not data.get("ErSkole"):
        return False
    return data.get("ErGrunnskole") is True or data.get("ErVideregaaendeSkole") is True


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
