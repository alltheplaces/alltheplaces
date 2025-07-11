import re

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class CfcIDSpider(Spider):
    name = "cfc_id"
    item_attributes = {"brand": "California Fried Chicken", "brand_wikidata": "Q5020502"}

    def start_requests(self):
        for page in range(1, 22):
            yield Request(f"https://www.cfcindonesia.com/index.php?page=peta&hal={page}")

    def parse(self, response: Response, **kwargs):
        restaurants = response.xpath("//tbody/tr/td/a/@href").getall()
        name = response.xpath("//tbody/tr/td/a/text()").getall()
        addresses = response.xpath("//tbody/tr/td/text()").getall()
        for restaurant, name, address in zip(restaurants, name, addresses):
            yield Request(
                f"https://www.cfcindonesia.com/{restaurant}",
                cb_kwargs={"name": name, "address": address},
                callback=self.parse_restaurant,
            )

    def parse_restaurant(self, response: Response, name, address):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = name
        item["addr_full"] = address
        location = re.findall(r"OpenLayers\.LonLat\(([ \d\.\-,]+)\)", response.text)
        item["lon"], item["lat"] = location[0].split(",")
        yield item
