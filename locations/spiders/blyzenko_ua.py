import scrapy

from locations.dict_parser import DictParser


class BlyzenkoUASpider(scrapy.Spider):
    name = "blyzenko_ua"
    item_attributes = {"brand": "Blyzenko", "brand_wikidata": "Q117670418"}
    allowed_domains = ["blyzenko.ua"]
    start_urls = [
        "https://blyzenko.ua/wp-json/wp/v2/shops-list",
    ]

    def parse(self, response):
        for store in response.json():
            acf_fields = store["acf_fields"]
            shop_map = acf_fields["shop_map"]

            item = DictParser.parse(acf_fields)
            item["phone"] = acf_fields["shop_tel"]
            item["street_address"] = shop_map["address"]
            item["lat"] = shop_map["lat"]
            item["lon"] = shop_map["lng"]
            # Google place ID? "place_id": "ChIJ1w8zu0jdOkcRUeY2kB95b3I",
            item["housenumber"] = shop_map["street_number"]
            item["street"] = shop_map["street_name"]
            item["city"] = shop_map["city"]
            item["state"] = shop_map["state"]
            item["postal_code"] = shop_map["post_code"]
            item["country"] = shop_map["country_short"]

            # Open 7 days a week? Data contains:
            #  {'shop_start': '08:00', 'shop_time_end': '22:00'}

            yield item
