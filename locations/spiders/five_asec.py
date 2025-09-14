from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class FiveAsecSpider(SitemapSpider):
    name = "five_asec"
    item_attributes = {"brand": "5àsec", "brand_wikidata": "Q2817899"}
    sitemap_urls = ["https://www.5asec.fr/sitemap.xml"]
    sitemap_rules = [(r"fr/fr/pressing/", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('string(//a[@class="address"]/span)').get().strip()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        yield item
