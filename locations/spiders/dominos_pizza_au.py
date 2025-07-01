from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaAUSpider(SitemapSpider):
    name = "dominos_pizza_au"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["www.dominos.com.au"]
    sitemap_urls = ["https://www.dominos.com.au/sitemap.aspx"]
    sitemap_rules = [(r"/store//[a-z-]+\d+", "parse")]
    user_agent = BROWSER_DEFAULT
    download_timeout = 180

    def parse(self, response):
        properties = {
            "ref": response.url.split("-")[-1],
            "branch": response.xpath('//div[@class="storetitle"]/text()').get().removeprefix("Domino's "),
            "addr_full": merge_address_lines(
                filter(None, map(str.strip, response.xpath('//a[@id="open-map-address"]/text()').getall()))
            ),
            "lat": float(response.xpath('//input[@id="store-lat"]/@value').get()),
            "lon": float(response.xpath('//input[@id="store-lon"]/@value').get()),
            "phone": response.xpath('//div[@id="store-tel"]/a/@href').get("").replace("tel:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        hours_text = " ".join(
            filter(
                None,
                map(str.strip, response.xpath('//span[@class="trading-day" or @class="trading-hour"]/text()').getall()),
            )
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)

        yield Feature(**properties)
