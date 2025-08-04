from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class TravismathewUSSpider(SitemapSpider):
    name = "travismathew_us"
    item_attributes = {"brand": "TravisMathew", "name": "TravisMathew", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://travismathew.com/sitemap.xml"]
    sitemap_rules = [(r"/pages/store/[\w-]$", "parse_item")]

    def parse_item(self, response):
        item = Feature()

        item["website"] = item["ref"] = response.url

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
