import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TotalHealthPharmacyIESpider(scrapy.Spider):
    name = "total_health_pharmacy_ie"
    item_attributes = {"brand": "TotalHealth Pharmacy", "brand_wikidata": "Q123165909"}
    start_urls = [
        "https://www.totalhealth.ie/store-locator",
    ]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"var pharmacies")]').re_first(r"var pharmacies = (\[.*\]);")
        )
        for store in data:
            item = DictParser.parse(store)
            item["ref"] = item["website"] = "https://www.totalhealth.ie" + store.get("link")
            item["phone"] = store.get("contactno")
            apply_category(Categories.PHARMACY, item)
            yield item
