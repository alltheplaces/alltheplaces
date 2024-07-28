from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class McgrathAUSpider(SitemapSpider, StructuredDataSpider):
    name = "mcgrath_au"
    item_attributes = {"brand": "McGrath", "brand_wikidata": "Q105290661"}
    allowed_domains = ["www.mcgrath.com.au"]
    sitemap_urls = ["https://mcgrathassets.blob.core.windows.net/sitemaps/sitemap-office.xml"]
    sitemap_rules = [("/offices/", "parse_sd")]
    wanted_types = ["RealEstateAgent"]

    def pre_process_data(self, ld_data):
        # Some coordinates are missing a minus in front of the latitude value.
        if ld_data.get("geo"):
            if float(ld_data["geo"]["latitude"]) > 0:
                ld_data["geo"]["latitude"] = str(-1 * float(ld_data["geo"]["latitude"]))

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        hours_string = " ".join(response.xpath('//div[@class="office-details__details-text"]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
