import chompjs

from locations.json_blob_spider import JSONBlobSpider
from locations.hours import OpeningHours, DAYS_IT


class IrenSpider(JSONBlobSpider):
    name = "iren"
    item_attributes = {
        "brand": "Iren",
        "brand_wikidata": "Q3801865",
        # "extras": Categories.SHOP_XYZ.value
    }
    start_urls = ["https://www.irenlucegas.it/assistenza/sportelli"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//div[@id="store-pin"]/@data-store').get()
        )

    def post_process_item(self, item, response, location):
        item["ref"] = location["cap"] # Or, is this postcode?

        # TODO: Category... door? Shopfront?
        #  'categoria': 'Sportello'

        # Parse hours where possible. This is a widely varied string
        oh = OpeningHours()
        oh.add_ranges_from_string(location["orario"], DAYS_IT)
        item["opening_hours"] = oh

        yield item

