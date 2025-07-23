import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.auchan_lu import MY_AUCHAN
from locations.structured_data_spider import StructuredDataSpider

AUCHAN = {"brand": "Auchan", "brand_wikidata": "Q758603"}
AUCHAN_SUPERMERCADO = {"brand": "Auchan Supermercado", "brand_wikidata": "Q105857776"}


class AuchanPTSpider(CrawlSpider, StructuredDataSpider):
    name = "auchan_pt"
    start_urls = ["https://www.auchan.pt/pt/lojas"]
    rules = [Rule(LinkExtractor(allow="StoreID="), callback="parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            if rule.get("opens") and rule.get("opens"):
                rule["opens"] = rule["opens"].strip()
                rule["closes"] = rule["closes"].strip()

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["addr_full"] = item.pop("street_address", "")
        item["lat"] = response.xpath('//*[@id="storeLatitude"]/@value').get()
        item["lon"] = response.xpath('//*[@id="storeLongitude"]/@value').get()
        if item["phone"]:
            item["phone"] = re.sub(r"(\(.+\))", "", item["phone"])
        item["email"] = item["email"].strip()
        if response.url.endswith(".html"):
            item["ref"] = response.url.removesuffix(".html").rsplit("-", 1)[1]
        else:
            item["ref"] = response.url.rsplit("=", 1)[1]

        store_type = response.xpath("//@data-store-type").get()
        if store_type == "Auchan":
            if item["name"].startswith("My Auchan "):
                item["branch"] = item.pop("name").removeprefix("My Auchan ")
                item.update(MY_AUCHAN)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif item["name"].startswith("Auchan Supermercado "):
                item["branch"] = item.pop("name").removeprefix("Auchan Supermercado ")
                item.update(AUCHAN_SUPERMERCADO)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif item["name"].startswith("Auchan "):
                item["branch"] = item.pop("name").removeprefix("Auchan ")
                item.update(AUCHAN)
                apply_category(Categories.SHOP_SUPERMARKET, item)
        elif store_type == "GasStation":
            item["branch"] = item.pop("name").removeprefix("Gasolineira ")
            item["opening_hours"] = "24/7"
            item.update(AUCHAN)
            apply_category(Categories.FUEL_STATION, item)
        else:
            self.logger.error("Unexpected type: {}".format(store_type))

        if services := response.xpath('//*[contains(@class,"services-item")]//span/text()').getall():
            services = [service.lower() for service in services]
            apply_yes_no(Extras.WIFI, item, "wifi grátis" in services)
            apply_yes_no("amenity:parking", item, "parque grátis" in services)
        yield item
