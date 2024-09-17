from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class CoopNOSpider(Spider):
    name = "coop_no"
    BRANDS = {
        "01": {"brand": "Coop Prix", "brand_wikidata": "Q5167705"},
        "02": {"brand": "Obs", "brand_wikidata": "Q5167707"},
        "03": {"brand": "Coop Mega", "brand_wikidata": "Q4581010"},
        "04": {"brand": "Coop Marked", "brand_wikidata": "Q5167703"},
        "07": {"brand": "Extra", "brand_wikidata": "Q11964085"},
        "08": {"brand": "Matkroken", "brand_wikidata": "Q11988679"},
        "41": {"brand": "Coop Byggmix", "brand_wikidata": "Q12714075"},
        "43": {"brand": "Obs BYGG", "brand_wikidata": "Q5167707"},
        "45": {"brand": "Coop Elektro", "brand_wikidata": "Q111534601", "extras": Categories.SHOP_ELECTRONICS.value},
    }
    allowed_domains = ["www.coop.no"]
    start_urls = ["https://www.coop.no/api/content/butikker?skip=0&count=10000"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json().get("stores"):
            url = "https://www.coop.no/api/content" + location["url"]
            yield JsonRequest(url=url, callback=self.parse_store)

    def parse_store(self, response):
        location = response.json()
        item = DictParser.parse(location)
        if brand := self.BRANDS.get(location.get("chainId", "")):
            item.update(brand)
        else:
            if location.get("chainId"):
                self.logger.error("Unknown brand ID: {}".format(location.get("chainId", "")))
        item["ref"] = location.get("metaInfo").get("canonicalUrl").split("-")[-1]
        item["street_address"] = item.pop("street", None)
        item["website"] = location.get("metaInfo").get("canonicalUrl")
        item["opening_hours"] = OpeningHours()
        for day_hours in location.get("openingHours", [])[:-1]:
            if day_hours.get("closed"):
                continue
            item["opening_hours"].add_range(DAYS[day_hours["dayOfWeek"] - 1], day_hours["from1"], day_hours["to1"])
            if day_hours.get("from2") and day_hours.get("to2"):
                item["opening_hours"].add_range(DAYS[day_hours["dayOfWeek"] - 1], day_hours["from2"], day_hours["to2"])
        yield item
