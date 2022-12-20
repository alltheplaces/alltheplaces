import scrapy

from locations.dict_parser import DictParser


class RemaxFrSpider(scrapy.Spider):
    name = "remax_fr"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.fr"]
    start_urls = ["https://www.remax.fr/Api/Reference/Regions2"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "languageid": "2",
        }
    }

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            item["ref"] = data.get("regionID")

            yield item
