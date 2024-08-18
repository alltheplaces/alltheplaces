from html import unescape

from chompjs import parse_js_object

from locations.hours import DAYS_HU, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class YettelHUSpider(JSONBlobSpider):
    name = "yettel_hu"
    item_attributes = {"brand": "Yettel", "brand_wikidata": "Q268578"}
    allowed_domains = ["www.yettel.hu"]
    start_urls = ["https://www.yettel.hu/elerhetoseg/uzletkereso"]

    def extract_json(self, response):
        locations_js = unescape(response.xpath('//div[@id="outlet-map"]/@data-markers').get())
        return parse_js_object(locations_js)

    def post_process_item(self, item, response, location):
        item["ref"] = location["code"]
        item["street_address"] = item.pop("addr_full", None)
        hours_string = " ".join(
            [f"{day_range}: {hours_range}" for day_range, hours_range in location["opening"].items()]
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_HU)
        yield item
