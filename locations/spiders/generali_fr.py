import json
import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GeneraliFRSpider(SitemapSpider):
    name = "generali_fr"
    item_attributes = {"brand": "Generali", "brand_wikidata": "Q670482", "name": "Generali"}
    sitemap_urls = ["https://agences.generali.fr/sitemap_index.xml"]
    sitemap_follow = ["sitemap_geo"]
    # City pages list the nearest agencies, so they overlap.
    sitemap_rules = [(r"/results$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature | Request]:
        if not (raw := response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()):
            self.logger.warning(f"No __NEXT_DATA__ in {response.url}")
            return
        if not (data := json.loads(raw)["props"]["pageProps"].get("dualFrameData")):
            self.logger.warning(f"No agency list in {response.url}")
            return
        pagination = data.get("paginationData") or {}
        if pagination.get("currentPage") == 1:
            for page in range(2, pagination.get("elementsNumber", 1) + 1):
                yield response.follow(f"{response.url}/{page}")

        for poi in data.get("poisListData", []):
            metadata = poi["metadata"]
            address = poi.get("address") or {}
            contacts = metadata.get("contacts") or {}
            item = Feature()
            item["ref"] = poi["code"]
            name = (metadata.get("details") or {}).get("Name") or ""
            # "GENERALI <place>" names the branch; any other name is the independent agent's firm.
            if place := re.match(r"GENERALI[\s-]+(.+)", name, flags=re.IGNORECASE):
                item["branch"] = place.group(1).title()
            elif name:
                item["operator"] = name.title()
            position = poi.get("position") or {}
            item["lat"] = position.get("Latitude")
            item["lon"] = position.get("Longitude")
            # AddressLine2 is ignored: it is often a postal box (BP), otherwise mostly a building or area name.
            item["street_address"] = (address.get("AddressLine1") or "").title()
            item["city"] = (address.get("City") or "").title()
            item["postcode"] = address.get("PostalCode")
            item["phone"] = contacts.get("Phone")
            item["email"] = (contacts.get("Mail") or "").lower()
            item["website"] = contacts.get("Web")
            if fax := contacts.get("Fax"):
                item["extras"]["fax"] = fax
            apply_category(Categories.OFFICE_INSURANCE, item)

            schedule = (poi.get("schedules") or {}).get("Defaultweekschedule") or []
            # IsOpen is false on every day when the agency has no hours entered, which is not "closed".
            if any(day["values"]["IsOpen"] for day in schedule):
                item["opening_hours"] = OpeningHours()
                for day in schedule:
                    if not day["values"]["IsOpen"]:
                        item["opening_hours"].set_closed(day["name"])
                    for rng in day["values"]["OpeningRanges"]:
                        begin, end = rng["BeginTime"], rng["EndTime"]
                        item["opening_hours"].add_range(
                            day["name"],
                            f'{begin["Hour"]:02d}:{begin["Minute"]:02d}',
                            f'{end["Hour"]:02d}:{end["Minute"]:02d}',
                        )
            yield item
