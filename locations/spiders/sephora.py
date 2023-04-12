import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.vapestore_gb import clean_address
from locations.user_agents import BROWSER_DEFAULT


class SephoraSpider(SitemapSpider):
    name = "sephora"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    allowed_domains = ["www.sephora.com"]
    download_delay = 5  # Requested by robots.txt
    user_agent = BROWSER_DEFAULT
    sitemap_urls = [
        "https://www.sephora.com/sephora-store-sitemap.xml",  # US
        "https://www.sephora.com/sephora-store-sitemap_en-CA.xml",  # CA
    ]
    sitemap_rules = [(r"/happening/stores/", "parse_store")]

    @staticmethod
    def parse_hours(rules) -> OpeningHours:
        opening_hours = OpeningHours()

        for day, hours in rules.items():
            if not day.endswith("Hours"):
                continue
            if not hours or not isinstance(hours, str):
                continue
            if "CLOSED" in hours:
                continue

            start_time, end_time = hours.split("-")

            opening_hours.add_range(
                day.replace("Hours", ""),
                open_time=start_time.strip(),
                close_time=end_time.strip(),
                time_format="%I:%M%p",
            )
        return opening_hours

    def parse_store(self, response):
        data = json.loads(response.xpath('//script[@id="linkStore"]/text()').get())
        for location in DictParser.get_nested_key(data, "stores"):
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location["address"]["address1"], location["address"]["address2"]])
            item["website"] = response.url
            item["phone"] = location["address"]["phone"]
            item["opening_hours"] = self.parse_hours(location["storeHours"])

            yield item
