import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AudiBeSpider(scrapy.Spider):
    name = "audi_be"
    item_attributes = {
        "brand": "Audi",
        "brand_wikidata": "Q23317",
    }
    allowed_domains = ["audi.be"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": BROWSER_DEFAULT,
        },
    }

    def start_requests(self):
        url = "https://dealerlocator.dieteren.be/api/locator.asmx/SearchEntities"
        payload = '{"request":{"TemplateID":11,"Sale":"N","AfterSale":"N","ETron":false,"AudiSport":false,"Aap":false,"Gte":false,"Language":"fr"}}'
        yield scrapy.Request(url=url, body=payload, method="POST", callback=self.parse)

    def parse(self, response):
        for row in response.json()["d"]["Dealers"]:
            item = Feature()
            item["ref"] = row.get("UTE")
            item["name"] = row.get("NAME")
            item["street_address"] = row.get("ADDRESS")
            item["city"] = row.get("CITY")
            item["postcode"] = row.get("ZIP")
            item["lat"] = float(row.get("GPSLAT").replace(",", "."))
            item["lon"] = float(row.get("GPSLONG").replace(",", "."))
            item["country"] = row.get("country")
            item["phone"] = row.get("TEL")
            item["website"] = row.get("URL")
            item["email"] = row.get("MAIL")
            apply_category(Categories.SHOP_CAR, item)
            yield item
