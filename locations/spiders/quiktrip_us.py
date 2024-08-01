from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class QuiktripUSSpider(SitemapSpider, StructuredDataSpider):
    name = "quiktrip_us"
    item_attributes = {"brand": "QuikTrip", "brand_wikidata": "Q7271953"}
    sitemap_urls = ["https://locations.quiktrip.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.quiktrip\.com/\w\w/[-'\w]+/[-.'()\w]+$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        services = response.xpath('//div[@class="Core-serviceName"]/text()').getall()

        if "Fuel Types" in services:
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        apply_yes_no(Extras.ATM, item, "ATM" in services)

        yield item
