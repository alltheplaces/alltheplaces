import re
import urllib.parse

from scrapy import Spider

from locations.dict_parser import DictParser


class KirklandsSpider(Spider):
    name = "kirklands"
    item_attributes = {
        "brand": "Kirkland's",
        "brand_wikidata": "Q6415714",
    }
    start_urls = ["https://www.kirklands.com/js/dyn/store_locator_all_stores.js"]
    ROBOTSTXT_OBEY = False
    requires_proxy = True

    def parse(self, response):
        location_objects = re.split(r"allStores\[\d+\] = ", response.text)[1:]
        location_list = []
        for location_obj in location_objects:
            loc_info = {}
            matches = re.findall(r"store\.(.*?) = (.*?);", location_obj)
            for key, value in matches:
                loc_info[key.strip()] = value.strip().strip("'").replace('"', "")
            location_list.append(loc_info)

        for location in location_list:
            if location:
                item = DictParser.parse(location)
                item["branch"] = item.pop("name")
                item["street_address"] = " ".join([location["ADDRESS_LINE_1"], location["ADDRESS_LINE_2"]])
                item["website"] = "https://www.kirklands.com/custserv/store.jsp?storeName=" + urllib.parse.quote(
                    location["STORE_NAME"]
                )

                yield item
