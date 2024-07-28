from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TargetUSSpider(SitemapSpider, StructuredDataSpider):
    name = "target_us"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q1046951"}
    allowed_domains = ["target.com"]
    sitemap_urls = ["https://www.target.com/sitemap_stores-index.xml.gz"]
    wanted_types = ["DepartmentStore"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath('//h1[@data-test="@store-locator/StoreHeader/Heading"]/text()').get()

        if "SuperTarget" in response.text:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        yield item
