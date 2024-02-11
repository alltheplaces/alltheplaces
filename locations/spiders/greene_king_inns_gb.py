from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class GreeneKingInnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "greene_king_inns_gb"
    item_attributes = {
        "brand": "Greene King Inns",
        "brand_wikidata": "Q5564162",
        "extras": Categories.HOTEL.value,
    }
    sitemap_urls = ["https://www.greenekinginns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.greenekinginns\.co\.uk\/hotels\/[\w\-]+\/[\w\-]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = item["ref"].replace("gki-", "")
        yield item
