from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YhaAUSpider(SitemapSpider, StructuredDataSpider):
    name = "yha_au"
    item_attributes = {"brand": "Youth Hostels Association", "brand_wikidata": "Q8045885"}
    sitemap_urls = ["https://www.yha.com.au/en/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.yha\.com\.au\/hostels(?:\/[^\/]+){3}\/?$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("YHA ")
        item.pop("email", None)
        markers = loads(response.xpath("//div/@data-modeldata").get())
        item["lat"] = markers["MapMarkers"][0]["Latitude"]
        item["lon"] = markers["MapMarkers"][0]["Longitude"]
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
