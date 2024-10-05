import json

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HornbachDESpider(SitemapSpider, StructuredDataSpider):
    name = "hornbach_de"
    item_attributes = {"brand": "HORNBACH", "brand_wikidata": "Q685926"}
    sitemap_urls = ["https://www.hornbach.de/mein-markt/sitemapcms-de.xml"]
    sitemap_follow = ["mein-markt"]
    sitemap_rules = [("baumarkt", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["city"] = response.xpath('//div[@itemprop="addressLocality"]/text()').get()
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()
        open_times_data = response.xpath("//cms-market-info-box/@open-times").get()
        opening_hours = OpeningHours()
        for rule in json.loads(open_times_data)["openTimes"]:
            opening_hours.add_ranges_from_string(":".join([rule["day"].replace(".", ""), rule["time"]]), days=DAYS_DE)
        item["opening_hours"] = opening_hours
        yield item
