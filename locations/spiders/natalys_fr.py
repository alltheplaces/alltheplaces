import scrapy
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class NatalysFRSpider(SitemapSpider, StructuredDataSpider):
    name = "natalys_fr"
    item_attributes = {"brand": "Natalys", "brand_wikidata": "Q3336439", "extras": Categories.SHOP_BABY_GOODS.value}
    allowed_domains = [
        "boutiques.natalys.com",
    ]
    sitemap_urls = ["https://boutiques.natalys.com/sitemap_geo.xml"]
    sitemap_rules = [
        (r"boutiques\.natalys\.com/.*/.*/.*/results$", "discover_store_details"),
    ]

    def discover_store_details(self, response):
        urls = response.xpath('//a[contains(@href, "details")]/@href').extract()
        for url in urls:
            url = url.replace("\r\n", "")
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
