import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class XsportFitnessUSSpider(Spider):
    name = "xsport_fitness_us"
    item_attributes = {"brand": "XSport Fitness", "brand_wikidata": "Q122981991"}
    start_urls = ["https://www.xsportfitness.com/locations/index.aspx"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            re.search(r"'dataLocation' : '(data/locations-\d+\.xml)',", response.text).group(1),
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("/markers/marker"):
            item = Feature()
            item["ref"] = item["website"] = location.xpath("@web").get()
            if not item["website"].startswith("http"):
                item["website"] = "https://{}".format(item["website"])
            item["branch"] = location.xpath("@name").get()
            item["lat"] = location.xpath("@lat").get()
            item["lon"] = location.xpath("@lng").get()
            item["name"] = location.xpath("@type").get()
            item["street_address"] = location.xpath("@address").get()
            item["city"] = location.xpath("@city").get()
            item["state"] = location.xpath("@state").get()
            item["postcode"] = location.xpath("@postal").get()
            item["phone"] = location.xpath("@phone").get()
            if location.xpath("@hours1").get() == "Open 24/7":
                item["opening_hours"] = "24/7"

            yield item
