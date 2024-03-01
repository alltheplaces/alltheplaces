from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SparkasseDESpider(SitemapSpider, StructuredDataSpider):
    name = "sparkasse_de"
    item_attributes = {"brand": "Sparkasse", "brand_wikidata": "Q13601825"}
    sitemap_urls = ["https://www.sparkasse.de/sitemap/sitemap-filialfinder.xml"]

    def pre_process_data(self, ld_data, **kwargs):
        if lon := ld_data["geo"].get("longitude "):
            ld_data["geo"]["longitude"] = lon
        ld_data["telephone"] = ld_data.get("telephone", "").replace("/", "")

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "/geldautomaten/" in response.url:
            apply_category(Categories.ATM, item)
        elif "/filialen/" in response.url:
            apply_category(Categories.BANK, item)

        yield item
