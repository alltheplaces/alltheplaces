import scrapy

from locations.items import Feature

state = {
    "1": "AL",
    "3": "AZ",
    "5": "CA",
    "6": "CO",
    "7": "CT",
    "8": "DE",
    "13": "ID",
    "18": "KY",
    "20": "ME",
    "21": "MD",
    "22": "MA",
    "30": "NH",
    "31": "NJ",
    "32": "NM",
    "34": "NC",
    "39": "PA",
    "40": "RI",
    "43": "TN",
    "46": "VT",
    "47": "VA",
    "48": "WA",
    "49": "WV",
}


class GenesisRehabSpider(scrapy.Spider):
    name = "genesis_rehab"
    item_attributes = {"brand": "Genesis Rehab Services", "brand_wikidata": "Q5532813"}
    allowed_domains = ["genesishcc.com"]
    start_urls = [
        "https://www.genesishcc.com/page-data/findlocations/page-data.json",
    ]

    def parse(self, response):
        for rehab in response.json()["result"]["data"]["allNodeCenter"]["edges"]:
            data = rehab.pop("node")
            item = Feature()
            item["name"] = data["title"]
            item["state"] = state[str(data["field_state"])]
            item["city"] = data["field_city"]
            item["lat"] = data["field_latitude"]
            item["lon"] = data["field_longitude"]
            item["street_address"] = data["field_address_fl"]
            item["postcode"] = data["field_zip"]
            item["website"] = item["ref"] = "https://www.genesishcc.com" + data["path"]["alias"]
            yield item
