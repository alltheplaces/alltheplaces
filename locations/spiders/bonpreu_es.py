import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BonpreuESSpider(scrapy.Spider):
    name = "bonpreu_es"
    item_attributes = {"brand": "Bonpreu", "brand_wikidata": "Q11924747"}
    start_urls = ["https://www.bonpreuesclat.cat/cercador-d-establiments"]

    def parse(self, response):
        data = response.xpath(
            '//*[@id="portlet_cercadorestabliments_WAR_cercadorestablimentsportlet_INSTANCE_rIdyDd6D3TeG"]/div/div[2]/div/script[1]/text()'
        ).extract_first()
        data = re.sub("(?si)var establimentsJson =|function.*", "", data)
        for location in json.loads(data):
            if location["ensenya"] == "BONPREU" or location["ensenya"] == "BONPREU_RAPID":
                item = Feature()
                item["addr_full"] = location["direccio"]
                item["city"] = location["poblacio"]
                item["postcode"] = location["codiPostal"]
                item["phone"] = location["telefon"]
                item["lat"] = location["latitud"]
                item["lon"] = location["longitud"]
                item["website"] = item["ref"] = response.urljoin(location["page"])

                apply_category(Categories.SHOP_SUPERMARKET, item)

                yield item
