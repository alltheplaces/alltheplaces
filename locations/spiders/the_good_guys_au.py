import chompjs
import scrapy

from locations.hours import DAYS_FULL
from locations.structured_data_spider import StructuredDataSpider


class TheGoodGuysAUSpider(StructuredDataSpider):
    name = "the_good_guys_au"
    item_attributes = {"brand": "The Good Guys", "brand_wikidata": "Q7737217"}
    allowed_domains = ["www.thegoodguys.com.au"]
    start_urls = ["https://www.thegoodguys.com.au/store-locator"]
    time_format = "%I:%M%p"

    def parse(self, response):
        data_json = chompjs.parse_js_object(response.xpath('//div[@id="allStoreJson"]/text()').extract_first())
        for store in data_json["locations"]:
            yield scrapy.Request(store["url"], self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        # Linked data on the page deviates from specifications and
        # therefore needs correcting prior to being parsed.
        coordinates = "".join(ld_data.pop("geo").split())
        ld_data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": coordinates.split(",")[0],
            "longitude": coordinates.split(",")[1],
        }
        oh_spec = ld_data.pop("OpeningHoursSpecification", [])
        days_to_find = DAYS_FULL.copy()
        for day in oh_spec:
            day_name = day["dayOfWeek"].replace("http://schema.org/", "")
            if day_name in DAYS_FULL:
                days_to_find.remove(day_name)
        for day in oh_spec:
            if day["dayOfWeek"].replace("http://schema.org/", "") == "Today":
                day["dayOfWeek"] = "http://schema.org/" + days_to_find[0]
        ld_data["openingHoursSpecification"] = oh_spec

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("facebook")
        item.pop("image")

        yield item
