import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PudoTRSpider(scrapy.Spider):
    name = "pudo_tr"
    start_urls = ["https://webapp.pudo.com.tr/svc/api/v1.2/pudobox/pudoboxs/FilterPudobox?cityId=null&countyId=null"]
    item_attributes = {"brand": "pudo", "brand_wikidata": "Q131450632"}

    def parse(self, response):
        for item in response.json():
            d = DictParser.parse(item)
            d["state"] = item["city"]  # this is province / il in Turkish
            d["city"] = item["county"]  # this is district / ilçe in Turkish
            neighborhood = item["district"]
            addr_desc = item["addressDescription"]

            # if no neighborhood, address text only contains ilçe and il
            if neighborhood:
                d["addr_full"] = f"{item['addressText']} {item['county']} {item['city']}"
                apply_category({"addr:neighborhood": neighborhood}, d)  # mahalle in Turkish
            else:
                d["addr_full"] = item["addressText"]

            if addr_desc and addr_desc != neighborhood:
                apply_category({"addr:desc": addr_desc}, d)

            apply_category(Categories.PARCEL_LOCKER, d)

            # some of these boxes are in private areas (such as apartment complexes) and not accessible to public
            if item["isPrivate"]:
                apply_category({"access": "private"}, d)

            # all boxes are accessible 24/7
            d["opening_hours"] = "24/7"

            yield d
