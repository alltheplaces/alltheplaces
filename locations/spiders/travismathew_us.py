from urllib.parse import parse_qs, urlparse, urlunparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class TravismathewUSSpider(SitemapSpider):
    name = "travismathew_us"
    item_attributes = {"brand": "TravisMathew", "name": "TravisMathew", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://www.travismathew.com/sitemap.xml"]
    sitemap_rules = [(r"/stores?/T[0-9]+\?lat=[0-9.-]+&long=[0-9.-]+$", "parse_item")]
    sitemap_follow = ["Store"]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("/store/", "/stores/")
            yield entry

    def parse_item(self, response):
        item = Feature()

        url = urlparse(response.url)
        query = parse_qs(url.query)

        item["website"] = urlunparse(url._replace(query=None))
        item["lat"] = query["lat"][0]
        item["lon"] = query["long"][0]
        item["ref"] = url.path.split("/")[2]

        details = response.css(".s-details-box")
        item["branch"] = details.xpath("h4/text()").get()
        item["addr_full"] = "".join(details.xpath("h6/text()").getall())
        item["phone"] = details.css(".phonetxt ~ span::text").get().replace("TBD", "")

        oh = OpeningHours()
        for line in details.css(".dayHouralign"):
            oh.add_ranges_from_string("".join(line.css("*::text").getall()))
        item["opening_hours"] = oh

        item["image"] = response.urljoin(response.xpath("//@data-src").get())

        yield item
