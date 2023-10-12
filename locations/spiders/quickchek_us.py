from scrapy import FormRequest, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class QuickChekUSSpider(Spider):
    name = "quickchek_us"
    item_attributes = {"brand": "QuickChek", "brand_wikidata": "Q7271689"}
    allowed_domains = ["quickchek.com"]
    start_urls = ["https://quickchek.com/wp-admin/admin-ajax.php"]

    def start_requests(self):
        for url in self.start_urls:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            }
            formdata = {"action": "get_sorted_locations", "dist": "100000", "lat": "0", "lng": "0"}
            yield FormRequest(url=url, method="POST", formdata=formdata, headers=headers)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            if location["hours"] == "Open 24 Hours":
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                item["opening_hours"].add_ranges_from_string("Mo-Su: {}".format(location["hours"]))
            yield item
