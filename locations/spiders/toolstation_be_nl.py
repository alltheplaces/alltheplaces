import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NL, DAYS_NL, DELIMITERS_EN, OpeningHours


class ToolstationBENLSpider(Spider):
    name = "toolstation_be_nl"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    start_urls = ["https://www.toolstation.be/api/branches", "https://www.toolstation.nl/api/branches"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["site_id"]
            item["branch"] = item.pop("name", None)
            item["website"] = response.urljoin("/branches/{}".format(location["slug"]))

            item["addr_full"], *hours = re.split(r"<br\s*/?>", location["address_text"])
            hours = " ".join(hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                hours, days=DAYS_NL, closed=CLOSED_NL, delimiters=DELIMITERS_EN + ["t/m"]
            )
            if "zon- en feestdagen gesloten" in hours:
                item["opening_hours"].set_closed("Su")

            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item
