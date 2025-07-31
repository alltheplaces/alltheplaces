from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PitaPitCASpider(SitemapSpider, StructuredDataSpider):
    name = "pita_pit_ca"
    item_attributes = {"brand": "Pita Pit", "brand_wikidata": "Q7757289"}
    sitemap_urls = ["https://pitapit.ca/robots.txt"]
    sitemap_follow = ["restaurants"]
    sitemap_rules = [(r"^https://pitapit.ca/restaurants/([^/]+)/$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None

        lon = float(item["lon"])
        if lon > 0:
            item["lon"] = lon * -1

        item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.xpath('//a[@title="Switch to FR"]/@href').get()

        apply_category(Categories.FAST_FOOD, item)

        yield item
