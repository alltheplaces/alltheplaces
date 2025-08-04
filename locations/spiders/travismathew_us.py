from urllib.parse import parse_qs, urlparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class TravismathewUSSpider(SitemapSpider):
    name = "travismathew_us"
    item_attributes = {"brand": "TravisMathew", "name": "TravisMathew", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://travismathew.com/sitemap.xml"]
    sitemap_rules = [(r"/pages/store/[\w-]+$", "parse_item")]

    def parse_item(self, response):
        item = Feature()

        item["website"] = item["ref"] = response.url

        item["branch"] = response.xpath("//h4/text()").get()
        item["addr_full"] = response.xpath("//h6/text()").get()
        item["phone"] = response.xpath("//span[text()='Phone: ']/following-sibling::text()").get()

        google_url = urlparse(response.xpath("//iframe[@id='gmap_canvas']/@src").get())
        q = parse_qs(google_url.query)["q"][0]
        if q.startswith("place_id:"):
            item["extras"]["ref:google:place_id"] = q.removeprefix("place_id:")

        oh = OpeningHours()
        for line in response.xpath("//p[text()='This Week’s Hours:']/following-sibling::ul/li"):
            day = line.xpath(".//strong/text()").get()
            hours = "".join(line.xpath("text()").getall())
            oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh

        yield item
