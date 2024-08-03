from urllib.parse import parse_qs, urlparse

from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.linked_data_parser import LinkedDataParser


class CinemarkSpider(SitemapSpider):
    name = "cinemark"
    item_attributes = {"brand": "Cinemark", "brand_wikidata": "Q707530"}
    allowed_domains = ["cinemark.com"]
    sitemap_urls = ["https://www.cinemark.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.cinemark\.com\/theatres\/.",
            "parse",
        ),
    ]
    download_delay = 10  # Requested by robots.txt

    def parse(self, response):
        item = LinkedDataParser.parse(response, "MovieTheater")

        item["ref"] = "/".join(response.url.rsplit("/")[-2:])
        item["lat"], item["lon"] = parse_qs(
            urlparse(response.css(".theatreInfoCollapseMap").xpath("//a/img/@data-src").extract_first()).query
        )["pp"][0].split(",")

        if item["name"].endswith(" - NOW CLOSED"):
            set_closed(item)

        del item["image"]

        yield item
