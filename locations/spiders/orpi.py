from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider


class OrpiSpider(SitemapSpider, StructuredDataSpider):
    name = "orpi"
    item_attributes = {"brand": "Orpi", "brand_wikidata": "Q3356080"}
    sitemap_urls = ["https://www.orpi.com/sitemap-agences.xml"]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "")

        url = response.xpath("//a[contains(@href, 'google.com/maps')]/@href").get()
        if url is not None:
            item["lat"], item["lon"] = url_to_coords(url)

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
