import chompjs

from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class IrenITSpider(JSONBlobSpider):
    name = "iren_it"
    item_attributes = {"brand": "Iren", "brand_wikidata": "Q3801865", "extras": {"office": "energy_supplier"}}
    start_urls = ["https://www.irenlucegas.it/assistenza/sportelli"]
    no_refs = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//div[@id="store-pin"]/@data-store').get())

    def post_process_item(self, item, response, location):
        # TODO: Category... door? Shopfront?
        #  'categoria': 'Sportello'

        # Parse hours where possible. This is a widely varied string
        if location["orario"] is not None:
            oh = OpeningHours()
            oh.add_ranges_from_string(
                location["orario"],
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
            )
            item["opening_hours"] = oh

        yield item
