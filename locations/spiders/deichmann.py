from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DeichmannSpider(SitemapSpider, StructuredDataSpider):
    name = "deichmann"
    DEICHMANN = {"brand": "Deichmann", "brand_wikidata": "Q664543"}
    DOSENBACH = {"brand": "Dosenbach", "brand_wikidata": "Q2677329"}
    item_attributes = DEICHMANN
    sitemap_urls = [
        "https://stores.deichmann.com/sitemap.xml",
        "https://stores.dosenbach.ch/sitemap.xml",
    ]
    sitemap_rules = [
        (r"^https:\/\/stores\.deichmann\.com\/[a-z]{2}-[a-z]{2}\/[a-z]{2}(?:\/[-\w]+){3}$", "parse_sd"),
        (r"^https:\/\/stores\.dosenbach\.ch\/ch-de\/ch(?:\/[-\w]+){3}$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "dosenbach.ch" in response.url:
            item.update(self.DOSENBACH)

        item["ref"] = item["ref"].split("#")[1]

        # remove fields that aren't unique amongst stores
        item.pop("email")
        item.pop("image")
        item.pop("facebook")

        yield item
