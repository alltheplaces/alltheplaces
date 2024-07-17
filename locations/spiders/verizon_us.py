import datetime
import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VerizonUSSpider(SitemapSpider):
    name = "verizon_us"
    item_attributes = {"brand": "Verizon", "brand_wikidata": "Q919641"}
    sitemap_urls = ["https://www.verizon.com/robots.txt"]
    sitemap_rules = [(r"https://www.verizon.com/stores/city/[^/]+/[^/]+/$", "parse_store")]

    OPERATORS = {
        "Asurion FSL": {"operator": "Asurion FSL"},
        "BeMobile": {"operator": "BeMobile"},
        "Best Wireless": {"operator": "Best Wireless"},
        "Cellular Plus": {"operator": "Cellular Plus"},
        "Cellular Sales": {"operator": "Cellular Sales", "operator_wikidata": "Q5058345"},
        "Mobile Generation": {"operator": "Mobile Generation"},
        "R Wireless": {"operator": "R Wireless"},
        "Russell Cellular": {"operator": "Russell Cellular", "operator_wikidata": "Q125523800"},
        "TCC": {"operator": "The Cellular Connection", "operator_wikidata": "Q121336519"},
        "Team Wireless": {"operator": "Team Wireless"},
        "Victra": {"operator": "Victra", "operator_wikidata": "Q118402656"},
        "Wireless Plus": {"operator": "Wireless Plus"},
        "Wireless World": {"operator": "Wireless World"},
        "Wireless Zone": {"operator": "Wireless Zone", "operator_wikidata": "Q122517436"},
        "Your Wireless": {"operator": "Your Wireless"},
    }

    def parse_hours(self, store_hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()

        for day, time in store_hours.items():
            if time == "Closed Closed":
                opening_hours.set_closed(day)
            elif m := re.match(r"(\d\d:\d\d [AP]M) (\d\d:\d\d [AP]M)", time):
                opening_hours.add_range(day, *m.groups(), "%I:%M %p")

        return opening_hours

    def parse_store(self, response):
        script = response.xpath('//script[contains(text(), "cityJSON")]/text()').extract_first()
        if not script:
            return

        for store_data in json.loads(re.search(r"var cityJSON = (.*);", script).group(1))["stores"]:
            item = DictParser.parse(store_data)
            item["street_address"] = item.pop("addr_full")
            item["state"] = store_data["stateAbbr"]
            item["website"] = response.urljoin(store_data["storeUrl"])
            item["extras"]["start_date"] = datetime.datetime.strptime(store_data["openingDate"], "%d-%b-%y").strftime(
                "%Y-%m-%d"
            )

            if "Authorized Retailer" in store_data["typeOfStore"]:
                for operator, tags in self.OPERATORS.items():
                    if item["name"].startswith(operator):
                        item["branch"] = item.pop("name").removeprefix(operator).strip(" -")
                        item.update(tags)
                        break
            else:
                item["branch"] = item.pop("name")
                item["operator"] = self.item_attributes["brand"]
                item["operator_wikidata"] = self.item_attributes["brand_wikidata"]

            item["opening_hours"] = self.parse_hours(store_data.get("openingHours"))

            yield item
