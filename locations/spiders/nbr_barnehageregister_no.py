from __future__ import annotations

from typing import AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature


class NbrBarnehageregisterNOSpider(Spider):
    name = "nbr_barnehageregister_no"
    allowed_domains = ["data-nbr.udir.no"]

    api_base_url = "https://data-nbr.udir.no"
    page_size = 1000

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_entity_request(page=1)

    def make_entity_request(self, page: int) -> JsonRequest:
        url = "{}{}".format(
            f"{self.api_base_url}/v4/enheter",
            "?" + urlencode({"sidenummer": page, "antallperside": self.page_size}),
        )
        return JsonRequest(
            url=url,
            cb_kwargs={"page": page},
            headers={"Accept": "application/json"},
        )

    def parse(self, response: TextResponse, page: int) -> Iterable[Feature | JsonRequest]:
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
                headers={"Accept": "application/json"},
            )

        total_pages = payload.get("AntallSider")
        if isinstance(total_pages, int) and page < total_pages:
            yield self.make_entity_request(page=page + 1)

    def parse_enhet(self, response: TextResponse, summary: dict) -> Iterable[Feature]:
        data = response.json()

        # Exclude excluded kindergartens.
        if data.get("ErEkskludert") is True:
            return

        # If entity somehow is inactive or not a kindergarten after filtering, exclude it.
        if data.get("ErAktiv") is not True or data.get("ErBarnehage") is not True:
            return

        item = Feature()
        item["ref"] = data.get("Organisasjonsnummer") or summary.get("Organisasjonsnummer")
        item["name"] = data.get("Navn") or data.get("FulltNavn") or summary.get("Navn")

        # Set short name if full name differs from name
        if full_name := data.get("FulltNavn"):
            if full_name != item["name"]:
                item["short_name"] = item["name"]
                item["name"] = full_name

        # Website
        if website := data.get("Internettadresse"):
            website = website.strip()
            if website and not website.startswith(("http://", "https://")):
                website = "https://" + website.lstrip("/")
            item["website"] = website

        # Operator
        if data.get("ErOffentligBarnehage") is True:
            item["extras"]["operator:type"] = "government"
        elif data.get("ErPrivatBarnehage") is True:
            item["extras"]["operator:type"] = "private"

        # Address
        if address := data.get("Beliggenhetsadresse"):
            item["street_address"] = address.get("Adresse")
            item["postcode"] = address.get("Postnummer")
            item["city"] = address.get("Poststed")
            item["country"] = address.get("Land")
        if fylke := data.get("Fylke"):
            item["state"] = fylke.get("Navn")

        # Geolocation
        if koordinat := data.get("Koordinat"):
            lat = koordinat.get("Breddegrad")
            lon = koordinat.get("Lengdegrad")
            if lat is not None and lon is not None:
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                except (TypeError, ValueError):
                    lat_f = lon_f = 0.0
                # Filter out invalid placeholder coordinates
                if abs(lat_f) > 0.0001 or abs(lon_f) > 0.0001:
                    item["lat"] = lat_f
                    item["lon"] = lon_f

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
