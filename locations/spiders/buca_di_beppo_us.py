from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BucaDiBeppoUSSpider(Spider):
    name = "buca_di_beppo_us"
    item_attributes = {"brand": "Buca di Beppo", "brand_wikidata": "Q4982340", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["www.bucadibeppo.com"]
    start_urls = ["https://www.bucadibeppo.com/locations/"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "const geoObject = ")]/text()').get()
        js_blob = js_blob.split("const geoObject = ", 1)[1].split("};", 1)[0] + "}"
        geojson_feature_collection = parse_js_object(js_blob)

        for location in geojson_feature_collection["features"]:
            if location["properties"]["is_closed"]:
                continue
            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["ref"] = location["properties"]["api_id"]
            item["street_address"] = clean_address(
                [location["properties"].get("address_line_1"), location["properties"].get("address_line_2")]
            )
            item["addr_full"] = clean_address(location["properties"].get("address_formatted"))
            item["website"] = location["properties"]["location_url"]

            item["opening_hours"] = OpeningHours()
            for day_hours in location["properties"].get("more_hours", []):
                if day_hours["is_closed"]:
                    continue
                if day_hours["open_day"] != day_hours["close_day"]:
                    self.logger.error(
                        "Could not extract hours for provided range of days: {} to {} as this spider does not currently support multi-day ranges.".format(
                            day_hours["open_day"], day_hours["close_day"]
                        )
                    )
                    continue
                item["opening_hours"].add_range(
                    day_hours["open_day"].title(), day_hours["open_time"], day_hours["close_time"]
                )

            yield item
