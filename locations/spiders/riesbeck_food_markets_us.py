import chompjs
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class RiesbeckFoodMarketsUSSpider(CrawlSpider):
    name = "riesbeck_food_markets_us"
    item_attributes = {
        "brand": "Riesbeck's",
        "brand_wikidata": "Q28226114",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.riesbeckfoods.com"]
    start_urls = ["https://www.riesbeckfoods.com/stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r"\/stores\/(?!no-store-global-settings)[\w\-]+"),
            callback="parse",
            follow=False,
        )
    ]

    def parse(self, response):
        location = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var storeJsonData = ")]/text()').get()
        )
        item = DictParser.parse(location)
        item["ref"] = location["store_number"]
        item["street_address"] = clean_address([location.get("address_1"), location.get("address_2")])
        if item["phone"] and "\n" in item["phone"]:
            item["phone"] = item["phone"].split("\n", 1)[0]
        apply_yes_no(Extras.DELIVERY, item, location.get("has_delivery"), False)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["hours_md"])
        yield item
