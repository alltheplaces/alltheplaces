import chompjs
import scrapy
from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.items import Feature


class AlicePizzaSpider(scrapy.Spider):
    name = "alice_pizza"
    item_attributes = {
        "brand": "Alice Pizza",
        "brand_wikidata": "Q107481541",  # Known wikidata ID for Alice Pizza if it matches, otherwise we can just omit it
    }
    start_urls = ["https://www.alicepizza.it/pizzerie/"]

    def parse(self, response):
        script_content = response.xpath('//script[contains(text(), "var storeListData")]/text()').get()
        if not script_content:
            return

        # Extract the JS object safely
        js_str = script_content.split("var storeListData=")[-1]
        data = chompjs.parse_js_object(js_str)

        for store in data.get("features", []):
            properties = store.get("properties", {})
            geometry = store.get("geometry", {})

            if not geometry or not geometry.get("coordinates"):
                continue

            coords = geometry["coordinates"]
            if len(coords) < 2:
                continue

            lon, lat = coords[0], coords[1]
            if lat == 0 and lon == 0:
                continue

            item = Feature()
            item["ref"] = properties.get("url") or properties.get("name")
            item["name"] = properties.get("name")
            item["street_address"] = properties.get("address")
            
            # The city_name is often set to 'Italia' in some objects, but it's safe to use if populated correctly
            city = properties.get("city_name")
            if city and city.lower() != "italia":
                item["city"] = city

            item["phone"] = properties.get("phone")
            item["website"] = properties.get("url")
            item["lat"] = lat
            item["lon"] = lon

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "pizza"

            timetable = properties.get("timetable")
            if timetable:
                try:
                    oh = OpeningHours()
                    oh.add_ranges_from_string(
                        timetable,
                        days=DAYS_IT,
                        named_day_ranges=NAMED_DAY_RANGES_IT,
                        named_times=NAMED_TIMES_IT,
                        closed=CLOSED_IT,
                    )
                    item["opening_hours"] = oh.as_opening_hours()
                except Exception:
                    pass

            yield item
