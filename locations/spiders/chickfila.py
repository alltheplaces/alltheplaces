from scrapy.spiders import SitemapSpider

from locations.google_url import url_to_coords
from locations.linked_data_parser import LinkedDataParser


class ChickFilASpider(SitemapSpider):
    name = "chickfila"
    item_attributes = {"brand": "Chick-Fil-A", "brand_wikidata": "Q491516"}
    allowed_domains = ["chick-fil-a.com"]
    sitemap_urls = ["https://www.chick-fil-a.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www.chick-fil-a.com\/locations\/..\/.*$",
            "parse",
        ),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")

        # Note that their opening hours specification doesn't include closing times, so no opening hours for now
        item["ref"] = "-".join(response.url.rsplit("/", 2)[-2:])
        item["phone"] = response.xpath(
            "//a[@id='LocationDetail-PhoneNumber']/a/text()"
        ).extract_first()

        google_link = response.xpath(
            "//div[@id='map-modal']/div/div/a/@href"
        ).extract_first()
        if google_link:
            item["lat"], item["lon"] = url_to_coords(google_link)

        yield item
