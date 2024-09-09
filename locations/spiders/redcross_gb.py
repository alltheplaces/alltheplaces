from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class RedcrossGBSpider(SitemapSpider):
    name = "redcross_gb"
    item_attributes = {"brand": "British Red Cross", "brand_wikidata": "Q4970966"}
    sitemap_urls = ["https://www.redcross.org.uk/sitemap.xml"]
    sitemap_rules = [("/find-a-charity-shop/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if dirty_address := response.xpath('//div[@class="shop-details-location"]/p/text()').getall():
            address = clean_address(dirty_address).split(", ")
            if address[0]:  # Closed shops
                if "special" in address[-1]:  # Remove spurious text from address
                    address = address[:-1]
                item = Feature()
                item["addr_full"] = ", ".join(address)
                item["postcode"] = address[-1]
                item["ref"] = item["website"] = response.url
                extract_google_position(item, response)
                yield item
