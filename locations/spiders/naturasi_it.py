from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NaturasiITSpider(SitemapSpider, StructuredDataSpider):
    name = "naturasi_it"
    item_attributes = {"brand": "NaturaSì", "brand_wikidata": "Q60840755"}
    sitemap_urls = ["https://negozi.naturasi.it/sitemap/sitemap_1.xml"]
    sitemap_rules = [(r"https://negozi.naturasi.it/.*", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "city" in item:
            item["city"] = item["city"].split("(")[0]

        yield item
