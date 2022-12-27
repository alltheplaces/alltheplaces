from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class DickBlickSpider(SitemapSpider, StructuredDataSpider):
    name = "dick_blick"
    item_attributes = {"brand": "Dick Blick", "brand_wikidata": "Q5272692"}
    allowed_domains = ["www.dickblick.com"]
    sitemap_urls = ["https://www.dickblick.com/sitemap.aspx"]
    sitemap_rules = [(r"/stores/[-\w]+/[-\w]+/$", "parse_sd")]
    wanted_types = ["HobbyShop"]
    user_agent = BROSWER_DEFAULT

    def inspect_item(self, item, response):
        oh = OpeningHours()
        for day in response.xpath('//li[contains(@data-testid,"hours")]'):
            if day.xpath("./text()").get().strip() == "Closed":
                continue
            oh.add_range(
                day=day.xpath("normalize-space(./span/text())").get().strip(":")[:3],
                open_time=day.xpath("./text()").get().split(" - ")[0],
                close_time=day.xpath("./text()").get().split(" - ")[1],
                time_format="%I:%M%p",
            )
        item["opening_hours"] = oh.as_opening_hours()
        yield item
