import re
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.central_england_cooperative import set_operator


class AnPostIESpider(Spider):
    name = "an_post_ie"
    AN_POST = {"brand": "An Post", "brand_wikidata": "Q482490"}

    cats = {
        "POSTPOINT": {"post_office": "post_partner"},
        "Parcel Locker": Categories.PARCEL_LOCKER,
        "Post Office": Categories.POST_OFFICE,
        "PostPoint": {"post_office": "post_partner"},
    }

    def start_requests(self):
        yield JsonRequest(
            "https://www.anpost.com/AnPost/StoreLocatorServices.asmx/Search?name=%27%27&radius=2000&userLat=53.1879823&userLon=-7.981917&service=%27%27&type=%27%27"
        )

    def parse(self, response, **kwargs):
        for location in response.json()["d"]:
            item = DictParser.parse(location)
            item["street_address"] = None
            item["addr_full"] = merge_address_lines(
                [
                    location["Address1"],
                    location["Address2"],
                    location["Address3"],
                    location["Address4"],
                    location["Address5"],
                    location["Address6"],
                ]
            )
            item["postcode"] = location["EirCode"]
            item["country"] = "IE"
            item["website"] = urljoin("https://www.anpost.com/Store-Locator/", location["NameURL"])
            item["extras"]["collection_times"] = location["LastTimeOfPosting"]

            item["opening_hours"] = OpeningHours()
            for rule in location["OpeningHours"].split(";"):
                if "closed" in rule.lower():
                    continue
                day, times = rule.strip().split(" ", maxsplit=1)
                for start_time, end_time in re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", times):
                    item["opening_hours"].add_range(day, start_time, end_time)

            if cat := self.cats.get(location["Type"]):
                apply_category(cat, item)
            else:
                item["extras"]["type"] = location["Type"]
                self.crawler.stats.inc_value("an_post_ie/unmapped_category/{}".format(location["Type"]))

            set_operator(self.AN_POST, item)

            yield item
