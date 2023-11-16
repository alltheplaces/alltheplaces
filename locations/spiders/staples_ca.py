from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StaplesCASpider(SitemapSpider, StructuredDataSpider):
    name = "staples_ca"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q17149420"}
    sitemap_urls = ["https://stores.staples.ca/robots.txt"]
    sitemap_rules = [(r".+/office-supplies-\w\w-\d+\.html$", "parse_sd")]
    wanted_types = ["OfficeEquipmentStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"], item["branch"] = item["name"].removeprefix("About ").rsplit(" ", 1)
        item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.xpath(
            '//a[contains(@href, "https://locations.bureauengros.com/")]/@href'
        ).get()

        item["website"] = (
            item["extras"]["website:fr"] if item["name"] == "Bureau en Gros" else item["extras"]["website:en"]
        )

        apply_category(Categories.SHOP_STATIONERY, item)

        yield item
