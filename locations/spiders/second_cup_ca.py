from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FR
from locations.structured_data_spider import StructuredDataSpider


class SecondCupCASpider(SitemapSpider, StructuredDataSpider):
    name = "second_cup_ca"
    item_attributes = {"brand": "Second Cup", "brand_wikidata": "Q862180"}
    sitemap_urls = ["https://secondcup.com/sitemap_index.xml"]
    sitemap_follow = ["locations"]
    sitemap_rules = [(r"^https://secondcup\.com/location/.*/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "openingHours" in ld_data:
            item["opening_hours"].add_ranges_from_string(ld_data["openingHours"], days=DAYS_FR)

        item["name"] = None
        item["branch"] = response.xpath("//h1/text()").get()

        if float(item["lon"]) > 0:
            item["lon"] = item["lon"] * -1

        yield item
