from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_SR, OpeningHours


class LillyRSSpider(Spider):
    name = "lilly_rs"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lilly.rs"]
    start_urls = [
        "https://www.lilly.rs/phpsqlsearch_genjson.php?lat=44.8019&lng=20.4671&radius=10000&limit=10000&keyword=none"
    ]
    requires_proxy = "US"  # Cloudflare bot blocking is in use

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["naziv_prodavnice"]
            item["street_address"] = location["adresa"]
            item["city"] = location["naziv_grada"]
            item["phone"] = location["telefon"]
            item["opening_hours"] = OpeningHours()
            hours_string = "Pon-Pet: " + location["pon_pet"] + " Sub: " + location["sub"] + " Ned: " + location["ned"]
            item["opening_hours"].add_ranges_from_string(hours_string, DAYS_SR)
            yield item
