import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class FrasersGBSpider(JSONBlobSpider):
    name = "frasers_gb"
    item_attributes = {"brand": "House of Fraser", "brand_wikidata": "Q5928422"}
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    async def start(self):
        headers = {"content-type": "application/json"}
        url = "https://api-fras.prd.frasersgroup.services/graphql?op=getStoresByLocation"
        formdata = {
            "query": "query getStoresByLocation($countryCode: String!, $distanceUnit: DistanceUnit!, $latitude: String!, $longitude: String!, $maxDistance: Int!, $storeKey: String!) {\n getStoresByLocation(\n countryCode: $countryCode\n distanceUnit: $distanceUnit\n latitude: $latitude\n longitude: $longitude\n maxDistance: $maxDistance\n storeKey: $storeKey\n ) {\n ...store\n }\n}\n\nfragment store on Store {\n accessibility {\n ...storeAccessibility\n }\n address {\n ...storeAddress\n }\n code\n concessions {\n ...storeConcession\n }\n description\n distance\n distanceUnit\n googleMapsImage\n googleMapsLink\n latitude\n longitude\n name\n openingHours {\n ...storeOpeningHours\n }\n phoneNumber\n services {\n ...storeService\n }\n slug\n storeType\n}\n\nfragment storeAccessibility on StoreAccessibility {\n description\n iconUrl\n}\n\nfragment storeAddress on StoreAddress {\n country\n countryCode\n postCode\n town\n address\n}\n\nfragment storeConcession on StoreConcession {\n title\n iconUrl\n}\n\nfragment storeOpeningHours on StoreOpeningHours {\n day\n openingTime\n closingTime\n}\n\nfragment storeService on StoreService {\n title\n description\n}",
            "variables": {
                "countryCode": "GB",
                "distanceUnit": "Miles",
                "latitude": "53.880548243856985",
                "longitude": "-1.8156785746075244",
                "maxDistance": 500,
                "storeKey": "HOF",
            },
        }
        request_body = json.dumps(formdata)
        req = scrapy.Request(url=url, body=request_body, method="POST", headers=headers, callback=self.parse)
        yield req

    def parse(self, response):
        storedata = response.json()["data"]["getStoresByLocation"]
        for store in storedata:
            item = DictParser.parse(store)
            name = item["name"]
            if "Frasers" in name or name.endswith("FRA"):
                item["name"] = "Frasers"
                item["brand"] = "Frasers"
                item["brand_wikidata"] = "Q124314052"
            else:
                item["name"] = "House of Fraser"
            item["branch"] = (
                name.removeprefix("Frasers ")
                .removeprefix("House of Fraser ")
                .removesuffix(" FRA")
                .removesuffix(" HOF")
                .removesuffix(" Frasers")
            )
            item["website"] = "https://www.houseoffraser.co.uk/stores" + item["ref"]

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item
