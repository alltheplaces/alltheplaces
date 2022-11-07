import scrapy

from locations.dict_parser import DictParser


class WoolworthsAUSpider(scrapy.Spider):
    name = "woolworths_au"
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q3249145"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=10000&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&postcode=*"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        data = response.json()

        for i in data["Stores"]:
            if not i["IsOpen"]:
                continue

            i["street_address"] = ", ".join(
                filter(None, [i["AddressLine1"], i["AddressLine2"]])
            )
            i["ref"] = i.pop("StoreNo")
            i["city"] = i.pop("Suburb")

            yield DictParser.parse(i)
