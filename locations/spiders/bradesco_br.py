import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BradescoBRSpider(scrapy.Spider):
    name = "bradesco_br"
    item_attributes = {"brand": "Bradesco", "brand_wikidata": "Q806181"}
    start_urls = [
        "https://wspf.bradesco.com.br/wsAtendimentoInstitucional/Site/Request.aspx?callback=rdaCallback&canal_id=1",
        "https://wspf.bradesco.com.br/wsAtendimentoInstitucional/Site/Request.aspx?callback=rdaCallback&canal_id=2",
    ]
    requires_proxy = True

    def parse(self, response):
        if "canal_id=2" in response.url:
            cat = Categories.ATM
        else:
            cat = Categories.BANK

        for poi in chompjs.parse_js_object(response.text)[0]:
            item = Feature()
            item["lat"] = poi[0]
            item["lon"] = poi[1]
            item["ref"] = poi[3] + "-" + poi[4]
            item["street_address"] = poi[7]
            item["city"] = poi[9]
            item["state"] = poi[10]
            item["postcode"] = poi[11]
            item["phone"] = poi[12]
            apply_category(cat, item)
            yield item
