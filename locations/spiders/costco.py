import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours, day_range
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CostcoSpider(SitemapSpider, StructuredDataSpider):
    name = "costco"
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
    oh = re.compile(r"(\w{3})(?:-(\w{3}))?.\s\s(\d\d:\d\d[AP]M) - (\d\d:\d\d[AP]M)")

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = response.xpath('//h1[@automation-id="warehouseNameOutput"]/text()').get()
        item["branch"] = name.removesuffix(" Warehouse").removesuffix(" Business Center")
        if "Business Center" in name:
            item["name"] = "Costco Business Center"
        else:
            item["name"] = "Costco"

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath(
            '//div/h2[@automation-id="warehouseHoursHeadingLabel"]/../div/time[@itemprop="openingHours"]/text()'
        ).getall():
            if m := re.match(self.oh, rule):
                days = day_range(m.group(1), m.group(2)) if m.group(2) else [m.group(1)]
                item["opening_hours"].add_days_range(days, m.group(3), m.group(4), "%I:%M%p")

        yield item
