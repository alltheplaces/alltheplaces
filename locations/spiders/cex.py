import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CexSpider(scrapy.Spider):
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
        item["name"] = store["storeName"]
        item["street_address"] = clean_address([store["addressLine1"], store["addressLine2"]])
        item["city"] = store["city"]
        item["state"] = store["county"]
        item["postcode"] = store["postcode"]
        item["website"] = "https://uk.webuy.com/site/storeDetail/?branchId=" + ref
        item["ref"] = ref
        item["image"] = ";".join(store["storeImageUrls"])

        oh = OpeningHours()
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            oh.add_range(
                day[:2].title(),
                store["timings"]["open"][day],
                store["timings"]["close"][day],
            )

        item["opening_hours"] = oh.as_opening_hours()

        yield item
