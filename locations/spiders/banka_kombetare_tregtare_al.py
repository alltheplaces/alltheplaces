from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class BankaKombetareTregtareALSpider(Spider):
    name = "banka_kombetare_tregtare_al"
    item_attributes = {"brand": "Banka Kombëtare Tregtare", "brand_wikidata": "Q806702"}
    start_urls = ["https://www.bkt.com.al/bkt-backoffice/Exchanges/GetAtmList"]

    def parse(self, response, **kwargs):
        for location in response.json()["Data"]:
            item = Feature()
            item["ref"] = location["oid"].strip()
            item["name"] = location["unitName"]
            item["street_address"] = location["unitAddress"]
            item["city"] = location["uniCity"]
            item["lat"] = location["unitCordNDec"]
            item["lon"] = location["unitCordEDec"]
            item["extras"]["fax"] = location["fax"]

            if location["unitType"] == "B":
                apply_category(Categories.BANK, item)
            elif location["unitType"] == "A":
                apply_category(Categories.ATM, item)

            yield item
