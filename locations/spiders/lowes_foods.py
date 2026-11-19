import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class LowesFoodsSpider(SitemapSpider):
    name = "lowes_foods"
    item_attributes = {"brand": "Lowes Foods", "brand_wikidata": "Q6693991"}
    allowed_domains = ["lowesfoods.com"]
    sitemap_urls = ["https://www.lowesfoods.com/sitemap.xml"]
    sitemap_rules = [(r".*store-locator/store-\d+$", "parse_store")]

    def parse_store(self, response):
        if response.xpath("//title/text()").get() == "Error":
            return

        city_state_zip = response.xpath("//div[@class='store-details__store-info']/ul/li[4]/text()").get().strip()

        map_data = response.xpath('//script[contains(text(), "initMap")]').get()

        item = Feature(
            ref=response.url.split("/")[-1],
            name=response.xpath("//div[@class='store-details__heading']/h1/text()").get().strip(),
            lat=re.search(r".*lat: (-?\d+\.\d+),.*", map_data).group(1),
            lon=re.search(r".*lng: (-?\d+\.\d+).*", map_data).group(1),
            street_address=response.xpath("//div[@class='store-details__store-info']/ul/li[2]/text()").get().strip(),
            city=city_state_zip.split(",")[0],
            state=city_state_zip.split(" ")[1],
            postcode=city_state_zip.split(" ")[2],
            country="United States",
            phone=response.xpath("//div[@class='store-details__store-info__phone']/a/text()").get().strip(),
            website=response.url,
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            response.xpath("//div[@class='store-details__heading']/h2/text()").get()
        )
        yield item
