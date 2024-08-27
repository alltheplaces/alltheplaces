from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class MasoutisGRSpider(Spider):
    name = "masoutis_gr"
    item_attributes = {"brand": "Masoutis", "brand_wikidata": "Q6783887"}
    allowed_domains = ["www.masoutis.gr"]

    def start_requests(self):
        formdata = {}
        yield FormRequest(
            url="https://www.masoutis.gr/api/masoutis/GetAllStoresEnabledLinks", method="POST", formdata=formdata
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            # {
            #     "Storeid": 382,
            #     "StoreDescr": "Θ. ΝΟΒΑ 7 - ΑΘΗΝΩΝ 26",
            #     "City": "ΝΑΥΠΑΚΤΟΣ",
            #     "Country": "ΑΙΤΩΛΟΑΚΑΡΝΑΝΙΑΣ",
            #     "KategoryID": "ΛΙΑΝΙΚΕΣ",
            #     "Langitude": "38.393701",
            #     "Longitude": "21.835841",
            #     "Phone": "2634021800",
            #     "PhotoData": "https://masoutisadm.masoutis.gr/main/ExportStore/382_sm.jpg",
            #     "IfParking": false,
            #     "Zip": "30300",
            #     "StoreDescrEn": "TH. NOVA - ATHINON 26",
            #     "CityEn": "NAYPAKTOS",
            #     "CountryEn": "AITOLOAKARNANIA",
            #     "KategoryIDEn": "SUPER MARKET",
            #     "IfCafe": false,
            #     "IfAtm": false,
            #     "IFgroceryShop": true,
            #     "IFbutchershop": true,
            #     "IfFishShop": false,
            #     "IFGasStation": false,
            #     "StoresSearchAll": "382 Θ. ΝΟΒΑ 7 - ΑΘΗΝΩΝ 26 TH. NOVA - ATHINON 26 ΑΙΤΩΛΟΑΚΑΡΝΑΝΙΑΣ AITOLOAKARNANIA",
            #     "IfReadyMeals": true,
            #     "IfBakery": false,
            #     "IfChildCare": false
            # },
            item["ref"] = location["Storeid"]
            item["image"] = location["PhotoData"]
            item["lat"] = location["Langitude"]
            item["lon"] = location["Longitude"]

            # TODO:  "KategoryIDEn": "SUPER MARKET" should probably override these extas
            apply_yes_no(Extras.ATM, item, location["IfAtm"])
            apply_yes_no("amentity=fuel", item, location["IFGasStation"])
            apply_yes_no("amentity=butcher", item, location["IFbutchershop"])
            apply_yes_no("shop=grocer", item, location["IFgroceryShop"])
            apply_yes_no("amenity=bakery", item, location["IfBakery"])
            apply_yes_no("shop=fish", item, location["IfFishShop"])
            apply_yes_no("childcare", item, location["IfChildCare"])
            apply_yes_no("amenity=cafe", item, location["IfCafe"])

            yield item
