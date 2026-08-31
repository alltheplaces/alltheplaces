import scrapy
from scrapy import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CexSpider(Spider):
    name = "cex"
    item_attributes = {"brand": "CeX", "brand_wikidata": "Q5055676", "country": "GB"}
    allowed_domains = ["wss2.cex.uk.webuy.io"]
    start_urls = ["https://wss2.cex.uk.webuy.io/v3/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for store in response.json()["response"]["data"]["stores"]:
            yield scrapy.Request(
                "https://wss2.cex.uk.webuy.io/v3/stores/" + str(store["storeId"]) + "/detail",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json()["response"]["data"]["store"]
        ref = response.url.split("/")[5]

        item = Feature()

        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        item["branch"] = store["storeName"]
        item["name"] = "CeX"
        item["street_address"] = clean_address([store["addressLine1"], store["addressLine2"]])
        item["city"] = store["city"]
        item["state"] = store["county"]
        item["postcode"] = store["postcode"]
        item["website"] = "https://uk.webuy.com/site/storeDetail/?branchId=" + ref
        item["ref"] = ref
        item["image"] = ";".join(store["storeImageUrls"])

        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            oh.add_range(day, store["timings"]["open"][day], store["timings"]["close"][day])

        item["opening_hours"] = oh

        yield item
