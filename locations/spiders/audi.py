from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class AudiSpider(Spider):
    name = "audi"
    item_attributes = {
        "brand": "Audi",
        "brand_wikidata": "Q23317",
    }
    graphql_url = "https://dev-dealer-graphql.apps.emea.vwapps.io/"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"clientid": "d7sfqwrxzu"}, "ROBOTSTXT_OBEY": False}

    def start_requests(self):
        market_request = JsonRequest(
            url=self.graphql_url,
            method="POST",
            data={"query": "query Dealer {\n  marketInfo {\n    markets {\n      market\n      scope\n    }\n  }\n}\n"},
            callback=self.request_market_data,
        )
        yield market_request

    def request_market_data(self, response):
        market_data = response.json().get("data").get("marketInfo").get("markets")
        for market in market_data:
            yield JsonRequest(
                url=self.graphql_url,
                method="POST",
                data={
                    "operationName": "Dealer",
                    "variables": {"market": market.get("market")},
                    "query": "query Dealer ($market: Market!) {\n    dealersByMarket(market: $market) {\n        dealers {\n            dealerId\n            name\n            services\n            latitude\n            longitude\n            phone: phoneInternational\n            fax: faxInternational\n            email\n            url\n            operator: chainId\n            country\n            openingHours {\n                departments {\n                    departmentName\n                    openingHours {\n                        timeRanges {\n                            openTime\n                            closeTime\n                        }\n                    }\n                }\n            }\n            address\n            houseNumber\n            street\n            city\n            zipCode\n        }\n    }\n}",
                },
            )

    def parse(self, response):
        data = response.json()
        store_data = data.get("data").get("dealersByMarket").get("dealers")
        if store_data:
            for store in store_data:
                properties = {
                    "ref": store.get("dealerId"),
                    "name": store.get("name"),
                    "addr_full": ", ".join(store.get("address")),
                    "housenumber": store.get("houseNumber"),
                    "street": store.get("street"),
                    "street_address": store.get("address")[0],
                    "city": store.get("city"),
                    "state": store.get("region"),
                    "phone": store.get("phone"),
                    "postcode": store.get("zipCode"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                }
                apply_category(Categories.SHOP_CAR, properties)
                yield Feature(**properties)
