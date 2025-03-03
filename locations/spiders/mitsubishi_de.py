import chompjs

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiDESpider(JSONBlobSpider):
    name = "mitsubishi_de"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.de/haendlersuche"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath("//partnersearch-root/@data-partners").get())

    def post_process_item(self, item, response, location):
        type_code = location.get("partnerTypID")
        if type_code in ["1", "5"]:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, True)
        elif type_code == "7":
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            self.logger.warning(f"Unknown type code: {type_code}, {item['name']}, {item['ref']}")
        self.crawler.stats.inc_value(f"atp/{self.name}/type_code/{type_code}")

        yield item
