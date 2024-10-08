import json

from scrapy import FormRequest, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBGSpider(Spider):
    name = "mcdonalds_bg"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.bg"]
    start_urls = ["https://mcdonalds.bg/restaurants/"]

    def parse(self, response):
        name_ids = response.xpath("//strong[@class='restaurant-item__title']/@data-restaurant-id").extract()

        for id in name_ids:
            yield FormRequest(
                url="https://mcdonalds.bg/wp-admin/admin-ajax.php",
                formdata={"action": "get_restaurant", "restaurant_id": id},
                callback=self.parse_restaurant,
                method="POST",
            )

    def parse_restaurant(self, response):
        location = json.loads(response.text)["data"]["data"]
        item = DictParser.parse(location)
        item["city"] = location.get("city", {}).get("city_name")
        if phone_numbers := location.get("phone_numbers", []):
            item["phone"] = phone_numbers[0]

        for benefit in location.get("benefits", []):
            apply_yes_no(Extras.WIFI, item, benefit.get("name") == "WiFi")
            apply_yes_no(Extras.DRIVE_THROUGH, item, benefit.get("name") == "McDrive™")
            if benefit.get("name") == "24/7":
                item["opening_hours"] = "24/7"

        apply_yes_no(Extras.DELIVERY, item, location.get("is_delivery_available"))

        if work_hours := location.get("work_hours", []):
            for work_hour in work_hours:
                oh = OpeningHours()
                oh.add_days_range(DAYS, work_hour.get("opens_at"), work_hour.get("closes_at"))
                if work_hour.get("label") == "Ресторант":
                    item["opening_hours"] = oh.as_opening_hours()
                elif work_hour.get("label") == "McDrive™":
                    item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()

        yield item
