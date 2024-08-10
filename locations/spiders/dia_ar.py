import scrapy

from locations.dict_parser import DictParser


class DiaARSpider(scrapy.Spider):
    name = "dia_ar"
    item_attributes = {"brand": "Dia", "brand_wikidata": "Q925132"}
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "REST-Range": "resources=0-4999",
        }
    }
    start_urls = [
        "https://diaonline.supermercadosdia.com.ar/api/dataentities/TI/search?_fields=active,address,bajaTemporal,city,geo,hours,id,name,new,province,service,tipo,whitelabel"
    ]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            if store.get("geo") != "0":
                item["lon"], item["lat"] = store["geo"].split(",")
            item["extras"] = {"type": store["tipo"]}
            yield item
