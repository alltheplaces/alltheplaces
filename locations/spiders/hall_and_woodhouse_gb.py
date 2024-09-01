from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class HallAndWoodhouseGBSpider(SitemapSpider):
    name = "hall_and_woodhouse_gb"
    item_attributes = {"brand": "Hall & Woodhouse", "brand_wikidata": "Q5642555"}
    sitemap_urls = ["https://www.hall-woodhouse.co.uk/pubs-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath('//meta[@property="og:title"]/@content').get()
        item["addr_full"] = response.xpath('//*[@class="noM"]/text()').get()
        item["phone"] = response.xpath("//*[contains(@href, 'tel:')]/@href").get()
        item["ref"] = item["extras"]["brand:website"] = response.url
        item["website"] = response.xpath('//a[contains(text(), "Website")]/@href').get()
        yield item
