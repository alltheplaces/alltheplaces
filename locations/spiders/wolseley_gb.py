import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class WolseleyGBSpider(SitemapSpider):
    name = "wolseley_gb"
    item_attributes = {"brand": "Wolseley", "brand_wikidata": "Q8030423"}
    sitemap_urls = ["https://www.wolseley.co.uk/sitemap.xml"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].endswith(".xml"):
                yield entry
            if m := re.search(r"\.uk/branch/(.+)/$", entry["loc"]):
                entry["loc"] = f"https://www.wolseley.co.uk/wcs/resources/store/10203/xstorelocator/{m.group(1)}"
                yield entry

    def parse(self, response, **kwargs):
        store = response.json()["storeLocation"]
        store["website"] = f'https://www.wolseley.co.uk/branch/{store["seoName"]}/'
        store["address"]["street_address"] = clean_address(
            [
                store["address"].pop("address1"),
                store["address"].pop("address2"),
                store["address"].pop("address3"),
            ]
        )
        item = DictParser.parse(store)

        item["image"] = ";".join(store["branchImageList"])

        if m := re.match(r"formerly (?:trading as )?(.+)$", store["secondaryName"]):
            item["extras"] = {"old_name": m.group(1)}

        oh = OpeningHours()
        for day in store["openingBusinessHours"]["hours"]:
            if day["closed"]:
                continue
            oh.add_range(day["dayOfWeek"], day["openingTime"], day["closingTime"])
        item["opening_hours"] = oh.as_opening_hours()

        yield item
