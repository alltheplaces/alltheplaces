import chompjs

from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class CinnabonRuSpider(JSONBlobSpider):
    name = "cinnabon_ru"
    item_attributes = {"brand": "Cinnabon", "brand_wikidata": "Q1092539", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://cinnabonrussia.com/locations/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var balloonArray = ")]/text()').get())

    def post_process_item(self, item, response, location):
        item["ref"] = location.get("number")
        item["lat"], item["lon"] = location.get("center")
        item["addr_full"] = item.pop("name")
        yield item
