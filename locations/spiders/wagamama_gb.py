from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone

# 2024-02-20 - Site has microdata, but it is broken :(


class WagamamaGBSpider(SitemapSpider):
    name = "wagamama_gb"
    item_attributes = {"brand": "Wagamama", "brand_wikidata": "Q503715"}
    allowed_domains = ["wagamama.com"]
    sitemap_urls = ["https://www.wagamama.com/sitemap.xml"]
    sitemap_rules = [("/restaurants/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url

        item["addr_full"] = merge_address_lines(response.xpath("//address//text()").getall())
        item["street_address"] = response.xpath('//meta[@itemprop="streetAddress"]/@content').get()
        item["city"] = response.xpath('//meta[@itemprop="addressLocality"]/@content').get()

        extract_google_position(item, response)
        extract_phone(item, response)
        yield item
