import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class TheCourierGuySpider(scrapy.Spider):
    name = "the_courier_guy"
    PUDO = {"brand": "pudo", "brand_wikidata": "Q116753323"}
    item_attributes = {"brand": "The Courier Guy", "brand_wikidata": "Q116753262"}
    allowed_domains = ["wp-admin.thecourierguy.co.za", "api-pudo.co.za"]

    def start_requests(self):
        yield scrapy.Request(
            url="https://wp-admin.thecourierguy.co.za/wp-json/acf/v3/service_points?per_page=10000",
            callback=self.parse_service_points,
        )
        yield scrapy.Request(
            url="https://api-pudo.co.za/api/v1/lockers-data?code=AIzaSyAjMJ4sIAmsTJYEFwI-nClSWvd_3SqbFA0",
            headers={"Authorization": "Bearer 5wfaWym3thWaOHbRk9AxNUqY4ArowSh1ppsjLz0Mf19bdf0c"},
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
            locker.update(locker.pop("detailed_address", {}))
            item = DictParser.parse(locker)
            item["ref"] = locker["code"]

            try:
                oh = OpeningHours()
                for day in locker.get("openinghours", []):
                    if day["day"] == "Public Holidays":
                        # TODO: parse public holidays
                        continue
                    oh.add_range(DAYS_EN.get(day["day"]), day["open_time"], day["close_time"], "%H:%M:%S")
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {e}")
                self.crawler.stats.inc_value("atp/hours/failed")

            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(self.PUDO)
            yield item
