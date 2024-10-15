import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns_gb"
    item_attributes = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}
    sitemap_urls = ["https://www.papajohns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.papajohns\.co\.uk\/stores\/([-.\w]+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data):
        item["website"] = response.url
        if item["extras"]["facebook"] == "https://www.facebook.com/papajohnsuk":
            item["extras"].pop("facebook")

        item["branch"] = item.pop("name")
        if m := re.search(r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", response.xpath('.//*[@class="map col"]/img/@src').get()):
            item["lon"], item["lat"] = m.groups()
        yield item
