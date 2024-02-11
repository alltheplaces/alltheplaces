import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class AuchanPTSpider(CrawlSpider, StructuredDataSpider):
    name = "auchan_pt"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}

    start_urls = ["https://www.auchan.pt/pt/lojas"]
    rules = [
        Rule(LinkExtractor(allow=r"StoreID="), callback="parse_sd"),
    ]

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            if rule.get("opens") and rule.get("opens"):
                rule["opens"] = rule["opens"].strip()
                rule["closes"] = rule["closes"].strip()

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = item.pop("street_address", "")
        item["lat"] = response.xpath('//*[@id="storeLatitude"]/@value').get()
        item["lon"] = response.xpath('//*[@id="storeLongitude"]/@value').get()
        if item["phone"]:
            item["phone"] = re.sub(r"(\(.+\))", "", item["phone"])
        item["email"] = item["email"].strip()
        store_type = response.xpath("//@data-store-type").get()
        if store_type == "MyAuchan":
            item["brand"] = "My Auchan"
        elif store_type == "GasStation":
            item["opening_hours"] = "24/7"
            item["nsi_id"] = "N/A"
            apply_category(Categories.FUEL_STATION, item)
        if services := response.xpath('//*[contains(@class,"services-item")]//span/text()').getall():
            services = [service.lower() for service in services]
            apply_yes_no(Extras.WIFI, item, "wifi grátis" in services)
            apply_yes_no("amenity:parking", item, "parque grátis" in services)
        yield item
