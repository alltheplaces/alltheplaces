from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DogHausUSSpider(Spider):
    name = "dog_haus_us"
    item_attributes = {"brand": "Dog Haus", "brand_wikidata": "Q105529843"}
    start_urls = ["https://locations.doghaus.com/modules/multilocation/?near_lat=0&near_lon=0&limit=200"]

    def parse(self, response):
        if response.json()["meta"]["next"]:
            self.logger.error("FIXME: too many results")
        for location in response.json()["objects"]:
            item = DictParser.parse(location)
            item["phone"] = location["phonemap_e164"]["phone"]
            item["branch"] = (
                location["custom_fields"]["display_name"]
                .removeprefix("Dog Haus ")
                .removeprefix("Biergarten ")
                .removeprefix("Kitchen ")
            )
            item["opening_hours"] = self.parse_hours(location["hours_by_type"]["primary"]["hours"])
            item["extras"]["happy_hours"] = self.parse_hours(
                location["hours_by_type"].get("happy_hour", {}).get("hours", [])
            ).as_opening_hours()
            item["ref"] = location["partner_location_id"].removeprefix("doghaus-")
            item["addr_full"] = location["geocoded"]
            del item["street"]
            item["street_address"] = location["street"]

            if "filter-kitchen" in location["services_tags"]:
                apply_category(Categories.CRAFT_CATERER, item)
            else:
                apply_category(Categories.FAST_FOOD, item)
                apply_yes_no(Extras.BAR, item, "filter-biergarten" in location["services_tags"])
                apply_yes_no(Extras.OUTDOOR_SEATING, item, "filter-biergarten" in location["services_tags"])

            yield item

    def parse_hours(self, hours):
        oh = OpeningHours()
        for row, day in zip(hours, DAYS):
            if len(row) == 0 or len(row[0]) < 2:
                continue
            for start, end in row:
                oh.add_range(day, start, end, time_format="%H:%M:%S")
        return oh
