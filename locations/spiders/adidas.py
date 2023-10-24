import json

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class AdidasSpider(Spider):
    name = "adidas"
    item_attributes = {"brand": "Adidas", "brand_wikidata": "Q3895"}
    start_urls = [
        "https://placesws.adidas-group.com/API/search?brand=adidas&geoengine=google&method=get&category=store&latlng=51%2C17&page=1&pagesize=5000&fields=name%2Cstreet1%2Cstreet2%2Caddressline%2Cbuildingname%2Cpostal_code%2Ccity%2Cstate%2Cstore_o+wner%2Ccountry%2Cstoretype%2Clongitude_google%2Clatitude_google%2Cstore_owner%2Cstate%2Cperformance%2Cbrand_store%2Cfactory_outlet%2Coriginals%2Cneo_label%2Cy3%2Cslvr%2Cchildren%2Cwoman%2Cfootwear%2Cfootball%2Cbasketball%2Coutdoor%2Cporsche_design%2Cmiadidas%2Cmiteam%2Cstella_mccartney%2Ceyewear%2Cmicoach%2Copening_ceremony%2Coperational_status%2Cfrom_date%2Cto_date%2Cdont_show_country&format=json&storetype=ownretail"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs):
        data = json.loads(response.body.replace(b"\n", b"\\n").replace(b"\r", b"\\r").replace(b"\\2", b"\\\\2"))
        for shop in data["wsResponse"]["result"]:
            item = DictParser.parse(shop)
            item["lat"] = shop["latitude_google"]
            item["lon"] = shop["longitude_google"]
            item["street_address"] = shop["street1"]
            yield item
