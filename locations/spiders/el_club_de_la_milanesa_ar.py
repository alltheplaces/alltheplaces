import scrapy

from locations.dict_parser import DictParser


class ElClubDeLaMilanesaARSpider(scrapy.Spider):
    name = "el_club_de_la_milanesa_ar"
    item_attributes = {"brand": "El Club de la Milanesa", "brand_wikidata": "Q117324078"}
    allowed_domains = ["elclubdelamilanesa.com"]
    start_urls = [
        "https://elclubdelamilanesa.com/wp-admin/admin-ajax.php?action=store_search&lat=-34.53438&lng=-58.46789",
    ]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item.pop("addr_full", None)
            item["street_address"] = store["address"]
            yield item
