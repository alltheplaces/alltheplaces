from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class GridserveGBSpider(SitemapSpider):
    name = "gridserve_gb"
    item_attributes = {"operator": "Gridserve", "operator_wikidata": "Q89575318"}
    sitemap_urls = ["https://www.gridserve.com/location-sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath("//*[@data-location]/@data-location").get()
        item["branch"] = response.xpath("//*[contains(@class, 'location__name')]/text()").get()
        item["addr_full"] = response.xpath("//*[contains(@class, 'location__address')]/text()").get()
        item["lat"] = response.xpath("//div[@class='gmap']/@data-lat").get()
        item["lon"] = response.xpath("//div[@class='gmap']/@data-lng").get()
        item["website"] = response.url
        apply_category(Categories.CHARGING_STATION, item)
        yield item
