from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SecuritestFRSpider(SitemapSpider, StructuredDataSpider):
    name = "securitest_fr"
    item_attributes = {"brand": "Sécuritest", "brand_wikidata": "Q64224992"}
    sitemap_urls = ["https://centre-controle-technique.securitest.fr/sitemap1.xml"]
    sitemap_rules = [(r"fr/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]
    drop_attributes = ["facebook"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = (
            item.pop("name", "")
            .lower()
            .removeprefix("sécuritest ")
            .removeprefix("contrôle technique ")
            .removeprefix("autosecurite ")
            .removeprefix("automobile ")
        )
        yield item
