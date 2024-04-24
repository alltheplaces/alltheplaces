import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TheCourierGuySpider(scrapy.Spider):
    name = "the_courier_guy"
    PUDO = {"brand": "pudo", "brand_wikidata": "Q116753323"}
    item_attributes = {"brand": "The Courier Guy", "brand_wikidata": "Q116753262"}
    allowed_domains = ["wp-admin.thecourierguy.co.za", "ksttcgzafunctionsv2-candidate.azurewebsites.net"]

    def start_requests(self):
        yield scrapy.Request(
            url="https://wp-admin.thecourierguy.co.za/wp-json/acf/v3/service_points?per_page=10000",
            callback=self.parse_service_points,
        )
        yield scrapy.Request(
            url="https://ksttcgzafunctionsv2-candidate.azurewebsites.net/api/tcg/terminal/get/all?code=1L4JQDYIBmEQr1Lq1I2kdPRCnfnJm4UU0nGP28LVsFaOcPv5vYCU3w==",
            callback=self.parse_lockers,
        )

    def parse_service_points(self, response):
        for point in response.json():
            item = DictParser.parse(point["acf"])

            item["ref"] = point["id"]
            item["name"] = point["acf"]["location_name"]

            location = point["acf"]["service_location"]
            if isinstance(location, dict):  # Can be boolean False
                item["city"] = location.get("city")
                item["country"] = location.get("country")
                item["lat"] = location.get("lat")
                item["lon"] = location.get("lng")
                item["postcode"] = location.get("post_code")
                item["state"] = location.get("state")
                item["street"] = location.get("street_name")
                item["street_address"] = location.get("address")
                item["housenumber"] = location.get("street_number")

            service_type = point["acf"].get("service_type")
            if service_type == "depot":
                apply_category(Categories.POST_DEPOT, item)
            elif service_type in ("branch", "kiosk"):
                apply_category(Categories.OFFICE_COURIER, item)

            yield item

    def parse_lockers(self, response):
        for locker in response.json():
            item = DictParser.parse(locker)
            item["postcode"] = locker.get("place", {}).get("postalCode")
            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(self.PUDO)
            yield item
