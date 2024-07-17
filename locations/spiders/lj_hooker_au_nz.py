from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class LJHookerAUNZSpider(Spider):
    name = "lj_hooker_au_nz"
    item_attributes = {"brand": "LJ Hooker", "brand_wikidata": "Q6456509"}
    allowed_domains = ["api01.ljx.com.au"]
    start_urls = [
        "https://api01.ljx.com.au/website/offices-v1?searchOrigin=residential-au",
        "https://api01.ljx.com.au/website/offices-v1?searchOrigin=residential-nz",
    ]

    def parse(self, response):
        for location in response.json()["offices"]:
            if location["name"] == "Training":
                continue
            item = DictParser.parse(location)
            item["ref"] = (
                location["linkUrl"]
                .replace("https://", "")
                .replace(".ljhooker.com.au", "")
                .replace(".ljhooker.co.nz", "")
            )
            item["street_address"] = clean_address(
                [location["address"].get("address1"), location["address"].get("address2")]
            )
            if ".com.au" in response.url:
                item["country"] = "AU"
            else:
                item["country"] = "NZ"
                item["city"] = item["city"].removesuffix(" NZ")
            item["website"] = location["linkUrl"]
            hours_string = ""
            for days_name, hours_range in location["tradingHours"].items():
                hours_string = f"{hours_string} {days_name}: {hours_range}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
