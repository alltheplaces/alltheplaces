from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PaversGBSpider(SitemapSpider):
    name = "pavers_gb"
    item_attributes = {"brand_wikidata": "Q7155843"}
    allowed_domains = ["pavers.co.uk"]

    sitemap_urls = ["https://www.pavers.co.uk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.pavers\.co\.uk\/store\/[\w\-]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get().removeprefix("Pavers Shoes")
        item["addr_full"] = merge_address_lines(response.xpath("//address/div/text()").getall())

        yield item
