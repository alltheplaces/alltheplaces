from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class OrpiSpider(SitemapSpider, StructuredDataSpider):
    name = "orpi"
    item_attributes = {"brand": "Orpi", "brand_wikidata": "Q3356080"}
    sitemap_urls = ["https://www.orpi.com/sitemap-agences.xml"]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "")

        extract_google_position(item, response)

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
