import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class LoblawsSpider(scrapy.Spider):
    name = "loblaws"
    allowed_domains = ["www.loblaws.ca"]
    start_urls = ("https://www.loblaws.ca/api/pickup-locations",)

    def parse(self, response):
        results = response.json()
        for i in results:
            if i["visible"] is False:
                continue
            if i["locationType"] == "STORE":
                if i["storeBannerId"] == "dominion":
                    brand = "Dominion Stores"
                    wikidata = "Q5291079"
                elif i["storeBannerId"] == "extrafoods":
                    brand = "Extra Foods"
                    wikidata = "Q5422144"
                elif i["storeBannerId"] == "zehrs":
                    brand = "Zehrs"
                    wikidata = "Q8068546"
                elif i["storeBannerId"] == "fortinos":
                    brand = "Fortinos"
                    wikidata = "Q5472662"
                elif i["storeBannerId"] == "rass":
                    brand = "Real Canadian Superstore"
                    wikidata = "Q7300856"
                elif i["storeBannerId"] == "loblaw":
                    brand = "Loblaws"
                    wikidata = "Q3257626"
                elif i["storeBannerId"] == "wholesaleclub":
                    brand = "Wholesale Club"
                    wikidata = "Q7997568"
                elif i["storeBannerId"] == "valumart":
                    brand = "Valu-mart"
                    wikidata = "Q7912687"
                elif i["storeBannerId"] == "superstore":
                    brand = "Atlantic Superstore"
                    wikidata = "Q4816566"
                elif i["storeBannerId"] == "maxi":
                    brand = "Maxi"
                    wikidata = "Q3302441"
                elif i["storeBannerId"] == "provigo":
                    brand = "Provigo"
                    wikidata = "Q3408306"
                elif i["storeBannerId"] == "nofrills":
                    brand = "No Frills"
                    wikidata = "Q3342407"
                else:
                    brand = "Your Independent Grocer"
                    wikidata = "Q8058833"

                properties = {
                    "brand": brand,
                    "brand_wikidata": wikidata,
                    "ref": i["storeId"],
                    "name": i["name"],
                    "lat": i["geoPoint"]["latitude"],
                    "lon": i["geoPoint"]["longitude"],
                    "street_address": clean_address([i["address"].get("line2"), i["address"].get("line1")]),
                    "city": i["address"]["town"],
                    "state": i["address"]["region"],
                    "postcode": i["address"]["postalCode"],
                    "country": i["address"]["country"],
                    "website": "https://www.loblaws.ca/store-locator/details/{}".format(i["storeId"]),
                }

                yield Feature(**properties)
