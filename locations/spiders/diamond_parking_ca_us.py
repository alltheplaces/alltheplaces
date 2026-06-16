import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DiamondParkingCAUSSpider(CrawlSpider):
    name = "diamond_parking_ca_us"
    item_attributes = {"brand": "Diamond Parking", "brand_wikidata": "Q5270887"}
    start_urls = ["https://diamond.permitpoint.com/Location", "https://diamondca.permitpoint.com/Location"]
    rules = [Rule(LinkExtractor(allow=r"/Location/Detail/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(
            response.xpath(
                '//aside[@id="location"]//h4[contains(text(),"Location Address:")]/following-sibling::text()'
            ).getall()
        )
        lat_lon = re.search(r"LatLng\((-?\d+\.\d+),(-?\d+\.\d+)\)", response.text)
        if lat_lon:
            item["lat"], item["lon"] = lat_lon.groups()
        item["website"] = item["ref"] = response.url
        if "diamondca" in response.url:
            item["country"] = "CA"
        else:
            item["country"] = "US"
        apply_category(Categories.PARKING, item)
        yield item
