from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class SaversGBSpider(SitemapSpider):
    name = "savers_gb"
    item_attributes = {"brand": "Savers", "brand_wikidata": "Q7428189"}
    sitemap_urls = ["https://www.savers.co.uk/sitemap.xml"]
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            if not entry["loc"].startswith("https://www.savers.co.uk/store/"):
                continue
            entry["loc"] = "https://www.savers.co.uk/store/page/{}".format(entry["loc"].split("/")[-1])
            yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["website"] = None
        item["street_address"] = merge_address_lines([item.pop("housenumber", None), item.pop("street", None)])
        item["branch"] = item.pop("name")
        item["ref"] = location["code"]
        item["addr_full"] = location["address"]["formattedAddress"]
        item["phone"] = location["address"]["phone"]

        item["opening_hours"] = OpeningHours()
        for rule in location["openingHours"]["weekDayOpeningList"]:
            item["opening_hours"].add_range(
                rule["weekDay"], rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"], "%I:%M %p"
            )

        yield item
