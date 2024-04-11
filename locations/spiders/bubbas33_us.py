import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class Bubbas33USSpider(SitemapSpider):
    name = "bubbas33_us"
    item_attributes = {"brand": "Bubba's 33", "brand_wikidata": "Q119359352"}
    sitemap_urls = ["https://www.bubbas33.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response, **kwargs):
        location = json.loads(re.search(r"window.__location__ = (\{.+\});", response.text).group(1))

        location["street_address"] = merge_address_lines([location.pop("address1"), location.pop("address2")])
        item = DictParser.parse(location)
        item["website"] = item["ref"] = response.url

        item["opening_hours"] = OpeningHours()
        for rule in location["schedule"]:
            item["opening_hours"].add_range(
                rule["day"], rule["hours"]["openTime"], rule["hours"]["closeTime"], time_format="%I:%M%p"
            )

        yield item
