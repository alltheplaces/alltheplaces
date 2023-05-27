from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import sitemap_urls_from_robots

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class KaiserPermanenteUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kaiser_permanente_us"
    item_attributes = {"brand": "Kaiser Permanente", "brand_wikidata": "Q1721601"}
    allowed_domains = ["healthy.kaiserpermanente.org"]
    sitemap_urls = ["https://healthy.kaiserpermanente.org/robots.txt"]
    sitemap_follow = ["/facilities/"]
    wanted_types = ["MedicalBusiness"]

    def _parse_sitemap(self, response):
        # SitemapSpider doesn't honour sitemap_follow while parsing robots.txt
        if response.url.endswith("/robots.txt"):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                if "/facilities/" in url:
                    yield Request(url, callback=self._parse_sitemap)
        else:
            yield from super()._parse_sitemap(response)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()

        cat = response.xpath("//@data-type").get()
        if cat == "Hospital":
            apply_category(Categories.HOSPITAL, item)
        elif cat == "Pharmacy":
            apply_category(Categories.PHARMACY, item)
        elif cat == "Vision Care":
            apply_category({"healthcare": "optometrist"}, item)
        elif cat == "Dialysis Center":
            apply_category({"healthcare": "dialysis"}, item)
        else:
            apply_category(Categories.CLINIC, item)
            item["extras"]["type"] = cat
            self.crawler.stats.inc_value(f"atp/kaiser_permanente_us/unmapped_category/{cat}")

        yield item
