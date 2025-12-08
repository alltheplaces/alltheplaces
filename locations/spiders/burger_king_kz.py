from chompjs import parse_js_object

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingKZSpider(JSONBlobSpider):
    name = "burger_king_kz"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.kz/ru/restaurants"]  # Have to get ru, kz and en are disallowed by robots.txt

    def extract_json(self, response):
        return parse_js_object(response.xpath('//script[contains(text(), "var restaurants = ")]/text()').get())

    def post_process_item(self, item, response, location):
        try:
            item["lat"] = location["map"].split(",")[0]
            item["lon"] = location["map"].split(",")[1]
        except:
            pass

        item["branch"] = item.pop("name")
        item["extras"]["branch:en"] = location["name_en"]
        item["extras"]["branch:kz"] = location["name_kz"]
        item["extras"]["branch:ru"] = location["name_ru"]

        item["street_address"] = item.pop("addr_full")

        item["extras"]["addr:street_address:en"] = location["address_en"]
        item["extras"]["addr:street_address:kz"] = location["address_kz"]
        item["extras"]["addr:street_address:ru"] = location["address_ru"]

        item["phone"] = "; ".join(location["phones"].split("<br />"))

        item["opening_hours"] = OpeningHours()
        if hours := location["worktime_en"]:
            item["opening_hours"].add_ranges_from_string(hours.replace(": 00", ":00").replace(" 0:00", " 23:59"))
        if item["opening_hours"].as_opening_hours() == "":
            if hours := location["worktime_ru"]:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(
                    hours.replace(" 0:00", " 23:59"), DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU
                )

        apply_yes_no(Extras.DRIVE_THROUGH, item, location["drive"] == 1)

        yield item
