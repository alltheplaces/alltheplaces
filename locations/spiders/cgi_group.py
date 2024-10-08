import scrapy

from locations.categories import Categories
from locations.items import Feature


class CgiGroupSpider(scrapy.Spider):
    name = "cgi_group"
    item_attributes = {"brand": "CGI Group", "brand_wikidata": "Q1798370", "extras": Categories.OFFICE_COMPANY.value}
    allowed_domains = ["cgi.com"]
    start_urls = (
        "https://www.cgi.com/en/offices?field_address_country_code=All&field_address_administrative_area=All&field_address_locality=All",
    )

    def parse(self, response):
        offices = response.xpath('//span[@class="region-wrapper"]/div[@class="vcard-wrapper"]')

        for office in offices:
            properties = {
                "name": " ".join(
                    filter(
                        None,
                        [
                            office.xpath('./div[@class="vcard"]/h4[@class="locality"]/text()').get(),
                            office.xpath('./div[@class="vcard"]/div[@class="adr"]/h4/text()').get(),
                        ],
                    )
                ).strip(),
                "street_address": office.xpath(
                    './div[@class="vcard"]/div[@class="adr"]/span[@class="street-block"]/text()'
                )
                .get()
                .strip(),
                "city": office.xpath('./div[@class="vcard"]/div[@class="adr"]/span[@class="locality"]/text()')
                .get()
                .strip(),
                "postcode": office.xpath(
                    './div[@class="vcard"]/div[@class="adr"]/span[@class="postal-code"]/text()'
                ).get(),
                "phone": office.xpath(
                    './div[@class="vcard"]/div[@class="adr"]/span[@class="telephone"]/a/text()'
                ).get(),
                "extras": {
                    "contact:fax": office.xpath(
                        './div[@class="vcard"]/div[@class="adr"]/span[@class="fax"]/a/text()'
                    ).get()
                },
            }

            if properties.get("phone"):
                properties["phone"] = properties["phone"].strip().replace("-", "").replace("(", "").replace(")", "")
            if properties["extras"].get("contact:fax"):
                properties["extras"]["contact:fax"] = (
                    properties["extras"]["contact:fax"].strip().replace("-", "").replace("(", "").replace(")", "")
                )

            if "(Mailing address)" in properties["name"]:
                continue

            properties["ref"] = hash(str(properties))

            yield Feature(**properties)
