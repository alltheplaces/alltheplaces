import json
import re

from scrapy.spiders import SitemapSpider 

from locations.items import Feature


class KindredHealthcareSpider(SitemapSpider):
    name = "kindred_healthcare"
    item_attributes = {"brand": "Kindred Healthcare", "brand_wikidata": "Q921363"}
    allowed_domains = ["www.kindredhospitals.com"]
    sitemap_urls = [
        "https://www.kindredhospitals.com/sitemap/sitemap.xml",
    ]
    sitemap_rules = [(r"https://www.kindredhospitals.com/locations/ltac/[\w-]+/contact-us", "parse_location")]

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
