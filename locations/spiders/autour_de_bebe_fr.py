import scrapy
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class AutourDeBebeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "autour_de_bebe_fr"
    item_attributes = {
        "brand": "Autour de Bébé",
        "brand_wikidata": "Q117842411",
        "extras": Categories.SHOP_BABY_GOODS.value,
    }
    allowed_domains = [
        "magasins.autourdebebe.com",
    ]
    sitemap_urls = ["https://magasins.autourdebebe.com/sitemap_geo.xml"]
    sitemap_rules = [
        (r"magasins\.autourdebebe\.com/.*/.*/.*/results$", "discover_store_details"),
    ]
    drop_attributes = {"image"}

    def discover_store_details(self, response):
        urls = response.xpath('//a[contains(@href, "details")]/@href').extract()
        for url in urls:
            url = url.replace("\r\n", "")
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
