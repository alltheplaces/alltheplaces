from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MochachosSpider(SitemapSpider):
    name = "mochachos"
    item_attributes = {
        "brand_wikidata": "Q116619117",
        "brand": "Mochachos",
    }
    allowed_domains = [
        "www.mochachos.com",
    ]
    sitemap_urls = ["https://www.mochachos.com/store-sitemap.xml"]
    sitemap_rules = [(r"/store/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        address = clean_address(response.xpath('//strong[contains(text(), "Address")]/../text()').getall())
        if not address:
            return
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["phone"] = "; ".join(response.xpath('//a[contains(@href, "tel:")]/@href').getall())
        item["addr_full"] = address
        item["branch"] = response.xpath('//*[@itemprop="headline"]/text()').get()
        yield item
