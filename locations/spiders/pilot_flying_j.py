import json

import scrapy

from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

PILOT = {"brand": "Pilot", "brand_wikidata": "Q64128179"}
FLYING_J = {"brand": "Flying J", "brand_wikidata": "Q64130592"}
ONE9 = {"brand": "ONE9"}
TOWN_PUMP = {"brand": "Town Pump", "brand_wikidata": "Q7830004"}


class PilotFlyingJSpider(scrapy.Spider):
    name = "pilot_flying_j"
    allowed_domains = ["pilotflyingj.com"]

    start_urls = ["https://locations.pilotflyingj.com/"]
    no_refs = True

    def parse(self, response):
        for href in response.xpath('//a[@data-ya-track="todirectory" or @data-ya-track="visitpage"]/@href').extract():
            yield scrapy.Request(response.urljoin(href))

        for item in response.xpath('//*[@itemtype="http://schema.org/LocalBusiness"]'):
            yield from self.parse_store(response, item)

    def parse_store(self, response, item):
        jsdata = json.loads(item.xpath('.//script[@class="js-map-config"]/text()').get())
        store = jsdata["entities"][0]["profile"]
        if "Dealer" in store["name"]:
            return
        store.update(store.pop("meta"))
        item = DictParser.parse(store)
        item["ref"] = None
        if phone := item.get("phone"):
            item["phone"] = phone.get("number")
        item["extras"]["fax"] = store.get("fax", {}).get("number")
        apply_yes_no(Fuel.DIESEL, item, True)
        apply_yes_no(Fuel.HGV_DIESEL, item, True)
        apply_yes_no(Access.HGV, item, True)
        apply_category(Categories.FUEL_STATION, item)
        item.update(self.brand_info(store["name"]))
        yield item

    def brand_info(self, name):
        if name in ["Pilot Licensed Location", "Pilot Travel Center"]:
            return PILOT
        elif name in ["Flying J Licensed Location", "Flying J Travel Center"]:
            return FLYING_J
        elif name == "Pilot Licensed Location - Town Pump":
            return TOWN_PUMP
        elif name == "ONE9 Travel Center":
            return ONE9
        return {}
