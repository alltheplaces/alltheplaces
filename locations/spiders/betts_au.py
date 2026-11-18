import csv
from io import StringIO

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class BettsAUSpider(PlaywrightSpider):
    name = "betts_au"
    item_attributes = {"brand": "Betts", "brand_wikidata": "Q118555401"}
    start_urls = ["https://www.betts.com.au/pages/store-locator"]
    allowed_domains = ["www.betts.com.au"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    no_refs = True

    def parse(self, response):
        csv_raw = response.xpath('//script[@id="store-locations"]/text()').get()
        rows = csv.DictReader(StringIO(csv_raw))
        for row in rows:
            item = DictParser.parse(row)
            item["branch"] = item.pop("name").removeprefix("Betts ")
            item["extras"]["ref:google:place_id"] = row["place_id"]
            apply_category(Categories.SHOP_SHOES, item)
            yield item
