from urllib.parse import parse_qs, urlparse

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class CinemarkSpider(SitemapSpider):
    name = "cinemark"
    item_attributes = {"brand": "Cinemark", "brand_wikidata": "Q707530"}
    allowed_domains = ["cinemark.com"]
    download_delay = 10
    sitemap_urls = ["https://www.cinemark.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.cinemark\.com\/theatres\/",
            "parse",
        ),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "MovieTheater")

        item["ref"] = "/".join(response.url.rsplit("/")[-2:])
        item["lat"], item["lon"] = parse_qs(
            urlparse(response.css(".theatreInfoCollapseMap").xpath("//a/img/@data-src").extract_first()).query
        )["pp"][0].split(",")

        yield item
