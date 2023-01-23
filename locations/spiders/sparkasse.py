from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class SparkasseSpider(SitemapSpider, StructuredDataSpider):
    name = "sparkasse"
    item_attributes = {"brand": "Sparkasse", "brand_wikidata": "Q13601825", "extras": Categories.BANK.value}
    sitemap_urls = ["https://www.sparkasse.de/sitemap.google-sitemap-filialfinder.xml"]

    def pre_process_data(self, ld_data, **kwargs):
        if lon := ld_data["geo"].get("longitude "):
            ld_data["geo"]["longitude"] = lon
        ld_data["telephone"] = ld_data.get("telephone", "").replace("/", "")
