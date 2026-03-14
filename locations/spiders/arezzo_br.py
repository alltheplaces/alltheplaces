import scrapy
import xmltodict
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_BR, OpeningHours, sanitise_day


class ArezzoBRSpider(scrapy.Spider):
    name = "arezzo_br"
    item_attributes = {"brand": "Arezzo", "brand_wikidata": "Q109569586"}
    start_urls = ["https://www.arezzo.com.br/arezzocoocc/v2/arezzo/stores?currentPage=0"]

    def parse(self, response, **kwargs):
        response_data = xmltodict.parse(response.body)["storeFinderSearchPage"]
        for store in response_data.get("stores", []):
            store.update(store.pop("address"))
            store["ref"] = store.pop("name")
            store["region"] = store["region"]["name"]
            store.pop("line1")  # The more specific house number and street are collected
            item = DictParser.parse(store)
            oh = OpeningHours()
            item["branch"] = item.pop("name").replace("Arezzo ", "").replace("AREZZO ", "")
            for rule in store["openingHours"]["weekDayOpeningList"]:
                if rule["closed"] != "false":
                    continue
                if day := sanitise_day(rule["weekDay"], DAYS_BR):
                    oh.add_range(
                        day,
                        rule["openingTime"].get("formattedHour"),
                        rule["closingTime"].get("formattedHour"),
                    )
            item["opening_hours"] = oh
            apply_category(Categories.SHOP_SHOES, item)
            yield item

        current_page = int(response_data["pagination"]["currentPage"])
        if current_page < int(response_data["pagination"]["totalPages"]):
            yield Request(url=f"https://www.arezzo.com.br/arezzocoocc/v2/arezzo/stores?currentPage={current_page + 1}")
