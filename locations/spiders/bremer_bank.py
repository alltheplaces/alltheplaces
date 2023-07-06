from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class BremerBankSpider(SitemapSpider):
    name = "bremer_bank"
    item_attributes = {"brand": "Bremer Bank", "brand_wikidata": "Q907603"}
    sitemap_urls = ["https://www.bremer.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]
    download_delay = 5.0

    def parse(self, response):
        properties = {
            "ref": response.url.split("/")[-1],
            "street_address": response.xpath('//div[@class="col-sm-12 col-lg-4"]/div/p/text()').extract_first().strip(),
            "phone": response.xpath('//a[@class="phoneLink"]/text()').extract_first(),
        }

        city, state, postcode = (
            response.xpath('//div[@class="col-sm-12 col-lg-4"]/div/p/text()')[2].extract().strip().split("\n")
        )

        properties["city"] = city.strip(",")
        properties["state"] = state.strip()
        properties["postcode"] = postcode.strip()

        extract_google_position(properties, response)

        yield Feature(**properties)
