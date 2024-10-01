from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class AmeripriseUSSpider(SitemapSpider):
    name = "ameriprise_us"
    item_attributes = {"brand": "Ameriprise Financial", "brand_wikidata": "Q2843129"}
    sitemap_urls = ["https://www.ameripriseadvisors.com/robots.txt"]
    sitemap_rules = [(r"/contact/$", "parse")]
    drop_attributes = {"image"}

    def parse(self, response):
        properties = LinkedDataParser.parse(response, "ContactPage")
        extract_google_position(properties, response)
        properties.update(
            {
                "ref": response.url,
                "website": response.urljoin(response.xpath('//*[.="Home"]//@href').get()),
                "name": response.css(".advisor-or-team-name ::text").get(),
                "street_address": response.css("[id$=AddressLine1] ::text").get(),
                "extras": {
                    "addr:unit": response.css("[id$=AddressLine2] ::text").get(),
                    "fax": response.css("[id$=AddressFax] ::text").get(),
                },
                "city": response.css("[id$=AddressCity] ::text").get(),
                "state": response.css("[id$=AddressState] ::text").get(),
                "postcode": response.css("[id$=AddressZip] ::text").get(),
                "phone": response.css("[id$=AddressPhone] ::text").get(),
                "email": response.css("[id$=AddressEmail] ::text").get(),
            }
        )
        properties["opening_hours"] = LinkedDataParser.parse_opening_hours(
            {"openingHours": response.css('[itemprop="openingHours"]::attr(content)').getall()}
        )
        yield Feature(properties)
