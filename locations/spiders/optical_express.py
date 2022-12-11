import json

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class OpticalExpressSpider(SitemapSpider):
    name = "optical_express"
    item_attributes = {
        "brand": "Optical Express",
        "brand_wikidata": "Q7098810",
        "country": "GB",
    }
    sitemap_urls = [
        "https://www.opticalexpress.co.uk/clinics-sitemap.xml",
    ]
    sitemap_rules = [
        (
            r"https:\/\/www\.opticalexpress\.co\.uk\/clinic-finder\/([\w-]+)\/([\w-]+)$",
            "parse",
        )
    ]

    def parse(self, response):
        ld = response.xpath('//script[@type="application/ld+json"]//text()').get()
        if not ld:
            return

        # They don't encode "description", breaking the json
        ld_item = json.loads(ld, strict=False)

        ld_item["name"] = (
            ld_item["name"]
            .replace("Optical Express Opticians &amp;amp; Laser Eye Surgery ", "")
            .replace("Optical Express Opticians &amp; Laser Eye Surgery ", "")
            .replace("Optical Express Opticians and Laser Eye Surgery ", "")
            .replace("Optical Express Opticians ", "")
            .replace("Optical Express Laser Eye Surgery ", "")
        )

        # This seems to be them badly encoding "Available by appointment only"
        ld_item["openingHours"] = ld_item["openingHours"].replace("Av , ", "")

        # This seems to be them badly encoding "Please call us on xxx to book an appointment for this clinic."
        ld_item["openingHours"] = ld_item["openingHours"].replace("Pl .", "")
        ld_item["openingHours"] = ld_item["openingHours"].replace("Pl ", "")

        # "Opening times and services may vary due to COVID-19"
        ld_item["openingHours"] = ld_item["openingHours"].replace("Op ,", "")
        ld_item["openingHours"] = ld_item["openingHours"].replace(", Op ", "")

        ld_item["openingHours"] = ld_item["openingHours"].replace("Alternate weeks only", "closed")
        ld_item["openingHours"] = ld_item["openingHours"].replace(
            "Opening times may vary. For appointments please call ahead or book online.",
            "closed",
        )

        # openingHours should be an array
        ld_item["openingHours"] = ld_item["openingHours"].split(", ")

        if ld_item.get("telephone") is None:
            ld_item["telephone"] = ld_item["address"]["telephone"]

        if ld_item.get("geo") is None:
            ld_item["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": response.xpath('//div[@id="lat"]/text()').get(),
                "longitude": response.xpath('//div[@id="lng"]/text()').get(),
            }

        item = LinkedDataParser.parse_ld(ld_item)

        item["ref"] = response.url
        item["website"] = response.url

        item["addr_full"] = response.xpath('//div[@id="address"]/text()').get()

        yield item
