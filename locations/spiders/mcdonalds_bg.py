import json

from scrapy import FormRequest, Spider

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsBGSpider(Spider):
    name = "mcdonalds_bg"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.bg"]
    start_urls = ["http://mcdonalds.bg/restaurants/"]

    def parse(self, response):
        name_ids = response.xpath("//strong[@class='restaurant-item__title']/@data-restaurant-id").extract()

        for id in name_ids:
            yield FormRequest(
                url="https://mcdonalds.bg/wp-admin/admin-ajax.php",
                formdata={"action": "get_restaurant", "restaurant_id": id},
                callback=self.parse_restaurant,
            )

    def parse_restaurant(self, response):
        poi = json.loads(response.text)
        data = poi.get("data", {}).get("data")
        item = DictParser.parse(data)

        item["city"] = data.get("city", {}).get("city_name")
        if phone_numbers := data.get("phone_numbers", []):
            item["phone"] = phone_numbers[0]

        for benefit in data.get("benefits", []):
            if benefit.get("name") == "WiFi":
                item["extras"]["internet_access"] = "wlan"
            if benefit.get("name") == "24/7":
                item["opening_hours"] = "24/7"
            if benefit.get("name") == "McDrive™":
                apply_yes_no("drive_through", item, True)

        if data.get("is_delivery_available"):
            apply_yes_no("delivery", item, True)

        yield item
