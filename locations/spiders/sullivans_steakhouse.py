import json

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class SullivansSteakhouseSpider(SitemapSpider):
    name = "saullivans_steakhouse"
    item_attributes = {"brand": "Sullivan's Steakhouse"}
    allowed_domains = ["www.sullivanssteakhouse.com"]
    sitemap_urls = ["https://www.sullivanssteakhouse.com/locations-sitemap.xml"]
    # download_delay = 1

    def parse(self, response):
        ld = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"][@class="yoast-schema-graph"]/text()'
            ).get()
        )

        for node in ld["@graph"]:
            if node["@type"] == "Restaurant":
                properties = {
                    "lat": node["geo"]["latitude"],
                    "lon": node["geo"]["longitude"],
                    "ref": response.url,
                    "website": response.url,
                    "name": node["name"].replace("Sullivan&#039;s Steakhouse ", ""),
                    "phone": node["telephone"],
                    "addr_full": node["address"]["streetAddress"]
                    .replace("  ", " ")
                    .replace("\t", "")
                    + ", United States",
                    "city": node["address"]["addressLocality"],
                    "state": node["address"]["addressRegion"],
                    "postcode": node["address"]["postalCode"],
                    "street_address": node["address"]["streetAddress"]
                    .replace("  ", " ")
                    .replace("\t", "")
                    .replace(node["address"]["postalCode"], "")
                    .replace(node["address"]["addressRegion"], "")
                    .replace(node["address"]["addressLocality"], "")
                    .replace("  ", "")
                    .strip(", "),
                    "country": "US",
                }

                yield GeojsonPointItem(**properties)
