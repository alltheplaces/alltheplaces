from locations.google_url import extract_google_position
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PureGymGBSpider(SitemapSpider, StructuredDataSpider):
    name = "puregym_gb"
    item_attributes = {
        "brand": "PureGym",
        "brand_wikidata": "Q18345898",
        "country": "GB",
    }
    allowed_domains = ["www.puregym.com"]
    sitemap_urls = ["https://www.puregym.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.puregym\.com\/gyms\/([\w-]+)\/$",
            "parse_sd",
        ),
    ]
    wanted_types = ["HealthClub"]

    def inspect_item(self, item, response):
        item["ref"] = response.xpath('//meta[@itemprop="gymId"]/@content').get()
        extract_google_position(item, response)

        yield item
