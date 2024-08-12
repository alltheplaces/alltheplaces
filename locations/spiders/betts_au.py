import csv
from io import StringIO

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser


class BettsAUSpider(Spider):
    name = "betts_au"
    item_attributes = {"brand": "Betts", "brand_wikidata": "Q118555401", "extras": Categories.SHOP_SHOES.value}
    start_urls = ["https://www.betts.com.au/pages/store-locator"]
    allowed_domains = ["www.betts.com.au"]
    no_refs = True

    def parse(self, response):
        csv_raw = response.xpath('//script[@id="store-locations"]/text()').get()
        rows = csv.DictReader(StringIO(csv_raw))
        for row in rows:
            item = DictParser.parse(row)
            item["branch"] = item.pop("name").removeprefix("Betts ")
            item["extras"]["ref:google"] = row["place_id"]
            yield item
