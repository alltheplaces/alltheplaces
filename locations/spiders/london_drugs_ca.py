import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class LondonDrugsCASpider(scrapy.Spider):
    name = "london_drugs_ca"
    item_attributes = {"brand": "London Drugs", "brand_wikidata": "Q3258955"}
    allowed_domains = ["www.londondrugs.com"]
    start_urls = ["https://www.londondrugs.com/on/demandware.store/Sites-LondonDrugs-Site/default/MktStoreList-All"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        stores = json.loads(response.body)
        for store in stores:
            item = DictParser.parse(store)
            if store.get("image"):
                item["image"] = "https://londondrugs.com" + store["image"]["url"]
            item["website"] = (
                "https://londondrugs.com/london-drugs-store-"
                + item["ref"]
                + "-"
                + item["city"].lower()
                + "/"
                + store["cityAliases"][0]
                + ".html"
            )
            for hours_type in store["storeHours"]:
                if hours_type["type"] == "Store Hours":
                    hours_text = ""
                    for day_hours in hours_type["storeHours"]:
                        day_range = day_hours["day"]
                        open_time = day_hours["hours"][0]
                        close_time = day_hours["hours"][1]
                        hours_text = f"{hours_text} {day_range}: {open_time} - {close_time}"
                    hours_text = hours_text.replace("& Holidays", "")
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(hours_text)
                    break
            yield item
