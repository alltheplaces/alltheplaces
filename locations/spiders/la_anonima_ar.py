from scrapy import Spider

from locations.dict_parser import DictParser


class LaAnonimaARSpider(Spider):
    name = "la_anonima_ar"
    start_urls = ["https://www.laanonima.com.ar/contents/themes/evolucionamos/bin/get_all_sucursales.php"]
    item_attributes = {"brand_wikidata": "Q6135985"}

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["phone"] = location["telefono"]
            item["addr_full"] = location["direccion"]
            item["extras"]["ref:branch"], item["branch"] = location["nombre"].split(" - ", 1)
            item["website"] = "https://www.laanonima.com.ar/" + location["url"]
            yield item
