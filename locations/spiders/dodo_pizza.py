from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DodoPizzaSpider(Spider):
    name = "dodo_pizza"
    item_attributes = {"brand": "Dodo Pizza", "brand_wikidata": "Q61949318"}
    allowed_domains = ["publicapi.dodois.io"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    # TODO: update list of countries in 2024
    countries = ["RU", "BY", "GB", "VN", "DE", "KZ", "CN", "KG", "LT", "NG", "PL", "RO", "SI", "TJ", "UZ", "EE", "US"]

    def start_requests(self):
        for country in self.countries:
            yield JsonRequest(
                url=f"https://publicapi.dodois.io/{country}/api/v1/unitinfo/all",
                callback=self.parse,
                meta={"country": country},
            )

    def parse(self, response):
        if pois := response.json():
            self.logger.info(f"Found {len(pois)} POIs for {response.meta['country']}")
            for poi in pois:
                yield from self.parse_poi(poi, response.meta["country"])

    def parse_poi(self, poi, country):
        # Type 1 is a restaurant, State 1 is restaurant is open
        if poi.get("Type") == 1 and poi.get("State") == 1:
            item = DictParser.parse(poi)
            item["ref"] = poi.get("UUId")
            item["name"] = poi.get("Alias")
            item["country"] = country
            item["street_address"] = poi.get("Address")
            # 'State' is not a state, but a state of the restaurant
            item["state"] = None
            item["addr_full"] = None

            if address_details := poi.get("AddressDetails"):
                item["city"] = address_details.get("LocalityName")
                item["street"] = " ".join(
                    filter(None, [address_details.get("StreetName"), address_details.get("StreetTypeName")])
                )
                item["housenumber"] = address_details.get("HouseNumber")

            apply_yes_no("delivery", item, poi.get("DeliveryEnabled"))
            apply_yes_no("payment:cards", item, poi.get("CardPaymentPickup"))
            self.parse_hours(item, poi)
            yield item

    def parse_hours(self, item, poi):
        if poi.get("IsAroundClockRestaurantWorkTime"):
            item["opening_hours"] = "24/7"
        else:
            if hours := poi.get("RestaurantWeekWorkingTime"):
                try:
                    oh = OpeningHours()
                    for hour in hours:
                        oh.add_range(
                            day=hour.get("DayAlias"),
                            open_time=f"{hour.get('WorkingTimeStart') // 3600:02}:{hour.get('WorkingTimeStart') % 3600 // 60:02}",
                            close_time=f"{hour.get('WorkingTimeEnd') // 3600:02}:{hour.get('WorkingTimeEnd') % 3600 // 60:02}",
                        )
                    item["opening_hours"] = oh.as_opening_hours()

                except:
                    self.crawler.stats.inc_value("failed_to_parse_hours")
