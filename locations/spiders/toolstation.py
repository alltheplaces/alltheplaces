import re
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NL, DAYS_NL, DELIMITERS_EN, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ToolstationSpider(SitemapSpider, StructuredDataSpider):
    name = "toolstation"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    sitemap_urls = ["https://www.toolstation.com/sitemap/branches.xml"]
    wanted_types = ["HardwareStore"]
    search_for_twitter = False
    search_for_facebook = False
    branch_api_urls = [
        "https://www.toolstation.be/api/branches",
        "https://www.toolstation.nl/api/branches",
    ]

    async def start(self) -> AsyncIterator[Any]:
        for url in self.branch_api_urls:
            yield JsonRequest(url=url, callback=self.parse_branch_api)
        async for request in super().start():
            yield request

    def parse_branch_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["site_id"]
            item["branch"] = item.pop("name", None)
            item["website"] = response.urljoin("/branches/{}".format(location["slug"]))

            address, *hours = re.split(r"<br\s*/?>", location["address_text"])
            item["addr_full"] = address
            hours = " ".join(hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                hours, days=DAYS_NL, closed=CLOSED_NL, delimiters=DELIMITERS_EN + ["t/m"]
            )
            if "zon- en feestdagen gesloten" in hours:
                item["opening_hours"].set_closed("Su")

            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if name := item.pop("name", None):
            item["branch"] = name.removeprefix("Toolstation ")
        if street_address := item.get("street_address"):
            item["street_address"] = re.sub(r"^Toolstation\b[^,]*,?", "", street_address).strip(", ") or None
        item["ref"] = item["website"].rsplit("/", 1)[-1]
        item["phone"] = None

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
