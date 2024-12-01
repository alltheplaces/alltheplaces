import chompjs
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class SemishagoffSpider(JSONBlobSpider):
    name = "semishagoff"
    item_attributes = {
        "brand": "Семишагофф",
        "brand_wikidata": "Q58003374",
    }
    start_urls = ["https://semishagoff.org/shops/"]

    def extract_json(self, response):
        objs = response.xpath('//script[contains(text(), "var resCoord = ")]/text()').get()
        return next(chompjs.parse_js_objects(objs))

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("name")
        if coodrinates := location.get("COORDINATES"):
            item["lat"], item["lon"] = coodrinates[0], coodrinates[1]
        time = Selector(text=location.get("BALOONCONTENT", "")).xpath("//time/span/text()").get()
        oh = OpeningHours()
        if time == "24 часа":
            oh.add_days_range(DAYS, "00:00", "24:00")
        else:
            oh.add_days_range(DAYS, time.split("-")[0], time.split("-")[1])
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
