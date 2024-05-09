import html

from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class SunLoanUSSpider(Spider):
    name = "sun_loan_us"
    item_attributes = {"brand": "Sun Loan", "brand_wikidata": "Q118725658"}
    allowed_domains = ["www.sunloan.com"]
    start_urls = [
        "https://www.sunloan.com/wp-admin/admin-ajax.php?action=sunloan_store_search&lat=31.968599&lng=-99.901813&max_results=10000&search_radius=20000&autoload=false&cat="
    ]

    def parse(self, response):
        for location in response.json():
            if not location.get("hours"):
                continue
            item = DictParser.parse(location)
            item["ref"] = str(location["id"])
            item["name"] = html.unescape(location["store"])
            item.pop("addr_full")
            item["street_address"] = clean_address([location["address"], location["address2"]])

            hours_html = Selector(text=location["hours"])
            hours_string = " ".join(hours_html.xpath("//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
