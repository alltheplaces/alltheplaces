import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


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
        hours_raw = response.xpath('//div[contains(@class, "opening-hours")]/dl/*/text()').getall()
        hours_raw = (
            " ".join(hours_raw)
            .upper()
            .replace("CLOSED", "00:00 AM - 00:00 AM")
            .replace("-", " ")
            .replace(" AM", "AM")
            .replace(" PM", "PM")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        oh = OpeningHours()
        for day in hours_raw:
            if day[0].title() not in DAYS_EN:
                continue
            if day[1] == "00:00AM" and day[2] == "00:00AM":
                continue
            oh.add_range(DAYS_EN[day[0].title()], day[1], day[2], "%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
