import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

BRANDS = {
    "%C4%B0ST%C4%B0KBAL": {"brand": "İstikbal", "brand_wikidata": "Q6031999"},
    "BELLONA": {"brand": "Bellona", "brand_wikidata": "Q6042498"},
    "MOND%C4%B0": {"brand": "Mondi", "brand_wikidata": "Q106803578"},
}


class ErciyesAnadoluHoldingTRSpider(scrapy.Spider):
    name = "erciyes_anadolu_holding_tr"
    download_delay = 3
    start_urls = ["https://brandapi.erciyes.com/api/ContactApi/GetCities"]

    def parse(self, response, **kwargs):
        for brand in BRANDS.keys():
            for city in response.json():
                yield scrapy.Request(
                    url=f"https://brandapi.erciyes.com/api/FirmApi/GetProvBrFirms?Brand={brand}&Code={str(int(city['CityCode']))}",
                    callback=self.parse_store,
                    cb_kwargs={"brand": brand},
                )

    def parse_store(self, response, **kwargs):
        for details in response.json():
            details["city"] = details.pop("Province")
            details["name"] = details.pop("FirmName")
            details["address"] = details.pop("Adres")
            details["email"] = details.pop("EMailAddress")
            item = DictParser.parse(details)
            item.update(BRANDS[kwargs["brand"]])
            apply_category(Categories.SHOP_FURNITURE, item)
            yield item
