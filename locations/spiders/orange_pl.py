from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class OrangePLSpider(AlgoliaSpider):
    name = "orange_pl"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486"}
    api_key = "7a46160ed01bb0af2c2af8d14b97f3c5"
    app_id = "0KNEMTBXX3"
    index_name = "OEPL_en"

    def post_process_item(self, item, response, location):
        item["street_address"] = clean_address([location.pop("street1"), location.pop("street2")])
        item["addr_full"] = clean_address(location["formatted_address"])
        item["lat"] = location["_geoloc"]["lat"]
        item["lon"] = location["_geoloc"]["lng"]
        item["country"] = location["country"]["code"]
        item["city"] = location["city"]["name"]
        item["website"] = f"https://salony.orange.pl/pl/{location['url_location']}"
        item.pop("name", None)
        self.parse_hours(item, location)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("formatted_opening_hours"):
            try:
                oh = OpeningHours()
                for day, hour in hours.items():
                    for times in hour:
                        oh.add_range(day, times.split("-")[0], times.split("-")[1], time_format="%I:%M%p")
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours {hours}: {e}")
