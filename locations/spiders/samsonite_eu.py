import scrapy
import xmltodict

from locations.dict_parser import DictParser


class SamsoniteEuSpider(scrapy.Spider):
    name = "samsonite_eu"
    item_attributes = {
        "brand": "Samsonite",
        "brand_wikidata": "Q1203426",
    }
    allowed_domains = ["samsonite.com"]

    def start_requests(self):
        country_eu = [
            "AL",
            "CZ",
            "DE",
            "DK",
            "CY",
            "AT",
            "BE",
            "BG",
            "CH",
            "EE",
            "EL",
            "ES",
            "FI",
            "FR",
            "HR",
            "HU",
            "IE",
            "IS",
            "IT",
            "LT",
            "LU",
            "NL",
            "NO",
            "LV",
            "ME",
            "MT",
            "MK",
            "LI",
            "PL",
            "SI",
            "SK",
            "TR",
            "UK",
            "RS",
            "SE",
            "PT",
            "RO",
        ]
        template = "https://storelocator.samsonite.eu/data-exchange/getDealerLocatorMapV2_Radius.aspx?s=sams&country={}&search=dealer&lat=48.85799300000001&lng=2.381153&radius=100000"
        for country in country_eu:
            yield scrapy.Request(url=template.format(country), callback=self.parse)

    def parse(self, response):
        data = xmltodict.parse(response.text)
        if data.get("dealers"):
            stores = data.get("dealers", {}).get("dealer")
            stores = stores if type(stores) == list else [stores]
            for store in stores:
                item = DictParser.parse(store)
                item["ref"] = store.get("fld_Deal_Id")
                item["street_address"] = store.get("fld_Deal_Address1")
                item["city"] = store.get("fld_Deal_City1")
                item["postcode"] = store.get("fld_Deal_Zip")
                item["country"] = store.get("fld_Coun_Name")
                item["phone"] = store.get("fld_Deal_Phone")
                item["email"] = store.get("fld_Deal_Email")

                yield item
