from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class KwikKopyAUSpider(SitemapSpider, StructuredDataSpider):
    name = "kwik_kopy_au"
    item_attributes = {"brand": "Kwik Kopy", "brand_wikidata": "Q126168253", "extras": Categories.SHOP_COPYSHOP.value}
    allowed_domains = ["kwikkopy.com.au"]
    sitemap_urls = ["https://kwikkopy.com.au/location-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/kwikkopy\.com\.au\/location\/\w+\/[\w\-]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data):
        item["lat"] = response.xpath('//div[@class="marker"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@class="marker"]/@data-lng').get()
        item["branch"] = item.pop("name").removeprefix("Kwik Kopy ")
        item["addr_full"] = item.pop("street_address", None)
        item.pop("image", None)  # Non-store-specific images should be ignored.
        item.pop("facebook", None)  # Non-store-specific Facebook pages should be ignored.
        yield item
