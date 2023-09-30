from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class McGrathAUSpider(SitemapSpider, StructuredDataSpider):
    name = "mcgrath_au"
    item_attributes = {"brand": "McGrath", "brand_wikidata": "Q105290661"}
    allowed_domains = ["www.mcgrath.com.au"]
    sitemap_urls = ["https://mcgrathassets.blob.core.windows.net/sitemaps/sitemap-office.xml"]
    sitemap_rules = [("/offices/", "parse_sd")]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        hours_string = " ".join(response.xpath('//div[@class="office-details__details-text"]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
