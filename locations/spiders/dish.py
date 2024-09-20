import scrapy

from locations.items import Feature

POSTALS = [
    "26601",
    "34604",
    "61749",
    "56425",
    "20716",
    "02818",
    "83227",
    "03226",
    "27330",
    "05669",
    "06023",
    "19946",
    "87036",
    "93645",
    "08515",
    "54443",
    "97754",
    "68856",
    "16835",
    "98847",
    "71369",
    "31044",
    "36750",
    "84642",
    "43317",
    "76873",
    "80827",
    "29061",
    "73114",
    "37132",
    "82638",
    "96706",
    "58463",
    "40033",
    "04426",
    "13310",
    "89310",
    "99756",
    "49621",
    "72113",
    "39094",
    "65064",
    "59464",
    "67427",
    "46278",
    "00720",
    "57501",
    "01757",
    "23921",
    "50201",
    "85544",
]


class DishSpider(scrapy.Spider):
    name = "dish"
    item_attributes = {"brand": "Dish", "brand_wikidata": "Q1199757"}
    allowed_domains = ["webapps.dish.com"]

    def start_requests(self):
        for postal in POSTALS:
            url = "https://webapps.dish.com/find-retailer/getretailershandler.ashx?Zip=" + postal + "&Miles=1000"

            yield scrapy.http.FormRequest(
                url,
                self.parse_store,
                method="GET",
            )

    def parse_store(self, response):
        store_data = response.json()

        for store in store_data:
            properties = {
                "ref": store["address"],
                "addr_full": store["address"],
                "lat": store["lat"],
                "lon": store["lng"],
                "name": store["storename"],
            }

            yield Feature(**properties)
