import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class ZikoAptekaPLSpider(Spider):
    name = "ziko_apteka_pl"
    item_attributes = {"brand": "Ziko Apteka", "brand_wikidata": "Q63432892"}
    allowed_domains = ["zikoapteka.pl"]
    start_urls = ["https://zikoapteka.pl/wp-admin/admin-ajax.php?action=get_pharmacies"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json().values():
            item = DictParser.parse(location)
            item["ref"] = location["mypostid"]
            item["city"] = location["city_name"][0]
            item.pop("state", None)
            if location.get("link"):
                item["website"] = "https://zikoapteka.pl/apteki" + location["link"] + "/"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                re.sub(r"\s+", " ", location["hours"].replace(".", "")), days=DAYS_PL
            )
            yield item
