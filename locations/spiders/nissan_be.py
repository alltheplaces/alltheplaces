import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature


class NissanSpider(scrapy.Spider):
    name = "nissan_be"
    item_attributes = {
        "brand": "Nissan",
        "brand_wikidata": "Q20165",
    }
    allowed_domains = ["nissan.be"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://nl.nissan.be/content/nissan_prod/nl_BE/index/dealer-finder/jcr:content/freeEditorial/contentzone_e70c/columns/columns12_5fe8/col1-par/find_a_dealer_6ff2.basic_dealers_by_location.json/page/1/_charset_/utf-8/size/-1/data.json"
    ]

    def parse(self, response):
        for data in response.json().get("dealers"):
            url = f"https://nl.nissan.be/content/nissan_prod/nl_BE/index/dealer-finder/jcr:content/freeEditorial/contentzone_e70c/columns/columns12_5fe8/col1-par/find_a_dealer_6ff2.extendeddealer.json/dealerId/{data.get('id')}/data.json"
            yield scrapy.Request(url=url, callback=self.parse_dealer)

    def parse_dealer(self, response):
        item = Feature()
        data = response.json()
        item["ref"] = data.get("dealerId")
        item["name"] = data.get("tradingName")
        item["street_address"] = data.get("address", {}).get("addressLine1")
        item["city"] = data.get("address", {}).get("city")
        item["postcode"] = data.get("address", {}).get("postalCode")
        item["lat"] = data.get("geolocation", {}).get("latitude")
        item["lon"] = data.get("geolocation", {}).get("longitude")
        item["country"] = data.get("country").upper()
        item["phone"] = data.get("contact", {}).get("phone")
        item["email"] = data.get("contact", {}).get("email")
        item["website"] = data.get("contact", {}).get("website")

        services = [s["name"] for s in data.get("dealerServices")]

        sales_list = [
            "Business Center",
            "Testrit",
            "Elektrische voertuigen",
            "Lichte bedrijfsvoertuigen",
            "Personenwagens",
        ]

        if any(s in services for s in sales_list):
            apply_category(Categories.SHOP_CAR, item)
            if "Erkend koetswerkhersteller" in services:
                apply_yes_no("service:vehicle:car_repair", item, True)
        else:
            if "Erkend koetswerkhersteller" in services:
                apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
