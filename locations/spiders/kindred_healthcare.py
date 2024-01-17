import json
import re

import scrapy

from locations.items import Feature


class KindredHealthcareSpider(scrapy.Spider):
    name = "kindred_healthcare"
    item_attributes = {"brand": "Kindred Healthcare", "brand_wikidata": "Q921363"}
    allowed_domains = ["www.kindredhospitals.com"]
    start_urls = [
        "https://www.kindredhospitals.com/sitemap/sitemap.xml",
    ]
    download_delay = 0.3

    def parse_location(self, response):
        is_location_page = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        )

        if is_location_page:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )

            facility_type = data["@type"]
            if facility_type == "Hospital":  # Keep refs consistent
                ref = re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).group(1)
            else:
                ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

            properties = {
                "name": data["name"],
                "ref": ref,
                "street_address": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data.get("contactPoint", {}).get("telephone"),
                "website": data.get("url") or response.url,
                "lat": float(data["geo"]["latitude"]),
                "lon": float(data["geo"]["longitude"]),
                "extras": {"facility_type": facility_type},
            }

            yield Feature(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath('//url/loc/text()[contains(., "locations")]').extract()

        for location_url in locations:
            # For transitional care hospitals, reduce redundant requests by using just the contact-us pages
            if "transitional-care-hospitals" in location_url and "contact-us" not in location_url:
                continue
            # Do the same thing for the behavioral health pages
            if "behavioral-health" in location_url and "contact-us" not in location_url:
                continue

            yield scrapy.Request(location_url, callback=self.parse_location)
