from urllib.parse import parse_qs, urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class CinemarkSpider(SitemapSpider, StructuredDataSpider):
    name = "cinemark"
    item_attributes = {"brand": "Cinemark", "brand_wikidata": "Q707530"}
    allowed_domains = ["cinemark.com"]
    sitemap_urls = ["https://www.cinemark.com/sitemap.xml"]
    sitemap_rules = [(r"/theatres/[^/]+/[^/]+$", "parse")]
    wanted_types = ["MovieTheater"]
    download_delay = 10  # Requested by robots.txt

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = "/".join(response.url.rsplit("/")[-2:])
        item["lat"], item["lon"] = (
            parse_qs(
                urlparse(response.xpath('//img[contains(@data-src, "dev.virtualearth.net")]/@data-src').get()).query
            )["pp"][0]
            .split(";", 1)[0]
            .split(",")
        )
        if item["name"].endswith(" - NOW CLOSED"):
            set_closed(item)

        del item["image"]

        yield item
