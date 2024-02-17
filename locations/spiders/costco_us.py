from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CostcoUSSpider(SitemapSpider, StructuredDataSpider):
    name = "costco_us"
    item_attributes = {
        "brand": "Costco",
        "brand_wikidata": "Q715583",
        "extras": Categories.SHOP_WHOLESALE.value,
    }
    allowed_domains = ["www.costco.com"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    sitemap_urls = ["https://www.costco.com/sitemap_lw_index.xml"]
    sitemap_follow = ["lw_l"]
    sitemap_rules = [(r"/warehouse-locations/[^.]+-(\d+)\.html$", "parse_sd")]
    requires_proxy = True
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = response.xpath('//h1[@automation-id="warehouseNameOutput"]/text()').get()
        item["branch"] = name.removesuffix(" Warehouse").removesuffix(" Business Center")
        if "Business Center" in name:
            item["name"] = "Costco Business Center"
        else:
            item["name"] = "Costco"

        yield item
