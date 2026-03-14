import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SalvosAUSpider(SitemapSpider):
    name = "salvos_au"
    item_attributes = {"brand": "Salvos", "brand_wikidata": "Q120646407"}
    sitemap_urls = ["https://www.salvosstores.com.au/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response):
        next_data = response.xpath('//*[@id="__NEXT_DATA__"]/text()').get() or ""
        json_data = json.loads(next_data)
        store_data = json_data.get("props", {}).get("pageProps", {}).get("store", {})

        if not store_data.get("StoreID"):
            return

        item = DictParser.parse(store_data)
        item["website"] = response.url
        item["branch"] = item.pop("name")

        oh = OpeningHours()
        for day, time in store_data["OpeningHours"].items():
            day = day
            if time == "Close":
                oh.set_closed(day)
            else:
                open_time = time["Opening"]
                close_time = time["Closing"]
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
        item["opening_hours"] = oh

        yield item
