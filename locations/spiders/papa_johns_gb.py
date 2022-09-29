from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns_gb"
    item_attributes = {
        "brand": "Papa John's",
        "brand_wikidata": "Q2759586",
        "country": "GB",
    }
    sitemap_urls = ["https://www.papajohns.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/www\.papajohns\.co\.uk\/stores\/(.+)\/home\.aspx$", "parse_sd")
    ]
    wanted_types = ["LocalBusiness"]

    def inspect_item(self, item, response):
        extract_google_position(item, response)
        item["website"] = response.url

        yield item
