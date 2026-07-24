import json

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class VoyageCareGBSpider(Spider):
    name = "voyage_care_gb"
    item_attributes = {"brand": "Voyage Care", "brand_wikidata": "Q134484515"}
    start_urls = ["https://www.voyagecare.com/your-support/"]

    def parse(self, response: Response, **kwargs):
        for location in json.loads(response.xpath("//@data-map-locations").get()):
            if "/?post_type=" not in location.get("guid"):
                yield scrapy.Request(
                    url=location.get("guid"),
                    callback=self.parse_details,
                    cb_kwargs={
                        "lat": location.get("meta").get("latitude"),
                        "lon": location.get("meta").get("longitude"),
                    },
                )

    def parse_details(self, response, **kwargs):
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath('//*[@class="text-content"]//h1//text()').get()
        item["addr_full"] = response.xpath('//*[@class="text-content"]//p//text()').get()
        item["lat"] = kwargs["lat"]
        item["lon"] = kwargs["lon"]
        item["website"] = item["ref"] = response.url
        apply_category(Categories.SOCIAL_FACILITY, item)
        yield item
