from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class FireAndRescueNSWAUSpider(SitemapSpider):
    name = "fire_and_rescue_nsw_au"
    item_attributes = {"operator": "Fire and Rescue New South Wales", "operator_wikidata": "Q5451532"}
    allowed_domains = ["www.fire.nsw.gov.au"]
    sitemap_urls = ["https://www.fire.nsw.gov.au/feeds/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.fire\.nsw\.gov\.au\/page\.php\?id=9210&station=\d+", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath("//main//h1/text()").get().strip(),
            "addr_full": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Address:")]/text()'
            )
            .get()
            .replace("Address:", "")
            .strip(),
            "state": "NSW",
            "phone": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Phone:")]/a/@href'
            )
            .get()
            .replace("tel:", ""),
            "website": response.url,
            "facebook": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Social media:")]/a/@href'
            ).get(),
        }
        extract_google_position(properties, response)
        apply_category({"amenity": "fire_station"}, properties)
        yield Feature(**properties)
