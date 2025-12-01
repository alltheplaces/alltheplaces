import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class AmericanMattressUSSpider(
    SitemapSpider,
):
    name = "american_mattress_us"
    sitemap_urls = ["https://cdn.avbportal.com/magento-media/sitemaps/bs0085/sitemap.xml"]
    item_attributes = {"brand": "American Mattress", "brand_wikidata": "Q126896153"}
    sitemap_rules = [("/locations/", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath("//h1/text()").get()
        item["ref"] = item["website"] = response.url
        item["street_address"] = response.xpath('//*[@class="dsg-contact-1__address-line"]/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="dsg-contact-1__address-line"][2]/text()').get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["lon"], item["lat"] = re.search(
            r"2d(-?\d+\.\d+)!3d(-?\d+\.\d+)!", response.xpath('//*[@class="dsg-contact-1__map"]/@src').get()
        ).groups()
        apply_category(Categories.SHOP_BED, item)
        yield item
