from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class KirklandsUSSpider(SitemapSpider):
    name = "kirklands_us"
    item_attributes = {"brand": "Kirkland's", "brand_wikidata": "Q6415714"}
    sitemap_urls = ["https://www.kirklands.com/store_sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//input[@id="storemaking"]/@value').get()
        item["street_address"] = response.xpath('//input[@id="storestreet"]/@value').get()
        item["city"] = response.xpath('//input[@id="storeCity"]/@value').get()
        item["state"] = response.xpath('//input[@id="storeState"]/@value').get()
        item["postcode"] = response.xpath('//input[@id="storeZip"]/@value').get()
        item["phone"] = response.xpath('//span[@itemprop="telephone"]/text()').get()
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('(//table[@class="hours"])[1]//tr'):
            item["opening_hours"].add_ranges_from_string(" ".join(rule.xpath("./td/text()").getall()))

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)

        yield item
