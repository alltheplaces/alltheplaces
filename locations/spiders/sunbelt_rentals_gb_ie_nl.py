import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SunbeltRentalsGBIENLSpider(Spider):
    name = "sunbelt_rentals_gb_ie_nl"
    item_attributes = {"brand": "Sunbelt Rentals", "brand_wikidata": "Q102396721"}
    allowed_domains = ["www.sunbeltrentals.co.uk"]
    start_urls = ["https://www.sunbeltrentals.co.uk/sitemap-location-1.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            if match := re.search(r"/depots/depot/([^/]+)/[^/]+$", url):
                yield JsonRequest(
                    url="https://www.sunbeltrentals.co.uk/webruntime/api/apex/execute?asGuest=true&htmlEncode=false",
                    data={
                        "namespace": "",
                        "classname": "@udd/01pSj000000ynu3",
                        "method": "getDepotData",
                        "isContinuation": False,
                        "cacheable": False,
                        "params": {"locationId": match.group(1)},
                    },
                    meta={"website": url},
                    callback=self.parse_depot,
                )

    def parse_depot(self, response: Response, **kwargs: Any) -> Any:
        depot = response.json()["returnValue"]
        address = depot.get("depotAddress") or {}

        item = Feature()
        item["ref"] = depot["locationId"]
        item["branch"] = depot["locationName"]
        item["website"] = response.meta["website"]
        item["lat"] = depot.get("depotLocationLattitude")
        item["lon"] = depot.get("depotLocationLongitude")
        item["street_address"] = address.get("street")
        item["city"] = address.get("city")
        item["postcode"] = address.get("postalCode")
        item["country"] = address.get("countryCode")
        item["phone"] = re.split(r"[/,]", depot.get("depotPhone") or "")[0]

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(depot.get("depotHours") or "")

        apply_category(Categories.SHOP_PLANT_HIRE, item)
        yield item
