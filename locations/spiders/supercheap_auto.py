import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SupercheapAutoSpider(SitemapSpider):
    name = "supercheap_auto"
    item_attributes = {"brand": "Supercheap Auto", "brand_wikidata": "Q7643119"}
    sitemap_urls = [
        "https://www.supercheapauto.com.au/sitemap-store_sitemap.xml",
        "https://www.supercheapauto.co.nz/sitemap-stores.xml",
    ]
    sitemap_rules = [(r"\/stores\/details\?s?id=", "parse_store")]

    def parse_store(self, response):
        data_raw = response.xpath('//div[@id="store-locator-details-map"]/@data-store-object').get()
        data_clean = data_raw.replace("&quot;", '"')
        store = json.loads(data_clean)
        item = DictParser.parse(store)
        item["ref"] = store["storeID"]
        item["street_address"] = item["street_address"].title()
        if item["country"] == "NZ":
            item.pop("state")
        item["website"] = response.url
        hours_string = " ".join(
            filter(None, response.xpath('//div[contains(@class, "opening-hours")]/dl[1]/*/text()').getall())
        )
        # Remove AM/PM from 24 hour timestamps (not supported by add_ranges_from_string function)
        if re.search(r"(?<!\d)(?:1[3-9]|2\d):\d{2}(?!\d)", hours_string):
            hours_string = re.sub(r"(?<=\d)\s*[AP]M", "", hours_string)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
