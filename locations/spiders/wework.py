from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class WeworkSpider(SitemapSpider, StructuredDataSpider):
    name = "wework"
    item_attributes = {"brand": "WeWork", "brand_wikidata": "Q19995004"}
    sitemap_urls = ["https://www.wework.com/sitemap.xml"]
    sitemap_rules = [("/buildings/", "parse_sd")]
    search_for_email = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").replace("WeWork Place", "")
        item["city"] = response.xpath("//optgroup/option[@selected]/text()").get()
        apply_category(Categories.OFFICE_COWORKING, item)
        yield item
