from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class WaffleHouseUSSpider(SitemapSpider):
    name = "waffle_house_us"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    sitemap_urls = ["https://locations.wafflehouse.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.wafflehouse.com/[^/]+/$", "parse")]
    wanted_types = ["Restaurant"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["street_address"] = response.xpath('//*[@property="business:contact_data:street_address"]/@content').get()
        item["city"] = response.xpath('//*[@property="business:contact_data:locality"]/@content').get()
        item["state"] = response.xpath('//*[@property="business:contact_data:region"]/@content').get()
        item["postcode"] = response.xpath('//*[@property="business:contact_data:postal_code"]/@content').get()
        item["phone"] = response.xpath('//*[@property="business:contact_data:phone_number"]/@content').get()
        item["lat"] = response.xpath('//*[@property="place:location:latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@property="place:location:longitude"]/@content').get()
        item["website"] = item["ref"] = response.url
        yield item
