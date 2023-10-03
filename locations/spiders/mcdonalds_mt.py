import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsMTSpider(SitemapSpider):
    name = "mcdonalds_mt"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.com.mt"]
    sitemap_urls = ["https://mcdonalds.com.mt/location-sitemap.xml"]
    sitemap_rules = [(r"\/location\/([\w\-]+)\/", "parse")]

    def parse(self, response):
        properties = {
            "ref": re.search(self.sitemap_rules[0][0], response.url).group(1),
            "name": response.xpath("//h1/text()").get().strip(),
            "addr_full": response.xpath("//div/p/text()").get().strip(),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "website": response.url,
        }

        oh = OpeningHours()
        for day in response.xpath(
            '//div[@class="elementor-tab-content elementor-clearfix"]/table[@class="location-hours-table"]//tr'
        )[0:6]:
            oh.add_range(
                day=day.xpath("./td[1]/text()").get(),
                open_time=day.xpath("./td[2]/text()").get().split(" - ")[0],
                close_time=day.xpath("./td[2]/text()").get().split(" - ")[1],
                time_format="%H:%M",
            )

        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
