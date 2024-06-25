from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RossmannPLSpider(SitemapSpider, StructuredDataSpider):
    name = "rossmann_pl"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    sitemap_urls = ["https://www.rossmann.pl/sitemap_shops.xml"]
    sitemap_rules = [("/drogerie/Drogeria-Rossmann-", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["name"] = ld_data["description"]

        # Country ends up in the city field for some reason
        item["country"] = item.pop("city")

        yield item
