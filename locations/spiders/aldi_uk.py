# -*- coding: utf-8 -*-
import json
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class AldiUKSpider(SitemapSpider):
    name = "aldi_uk"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171672"}
    allowed_domains = ["aldi.co.uk", "aldi.ie"]
    download_delay = 1.5
    sitemap_urls = [
        "https://www.aldi.co.uk/sitemap/store-en_gb-gbp",
        "https://www.aldi.ie/sitemap/store-en_ie-eur",
    ]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def parse(self, response):
        store_js = response.xpath(
            '//script[@type="text/javascript"]/text()'
        ).extract_first()
        json_data = re.search("gtmData =(.+?);", store_js).group(1)
        data = json.loads(json_data)

        geojson_data = response.xpath(
            '//script[@class="js-store-finder-initial-state"][@type="application/json"]/text()'
        ).extract_first()
        geodata = json.loads(geojson_data)

        properties = {
            "name": data["seoData"]["name"],
            "ref": geodata["store"]["code"],
            "street_address": data["seoData"]["address"]["streetAddress"],
            "city": data["seoData"]["address"]["addressLocality"],
            "postcode": data["seoData"]["address"]["postalCode"],
            "country": data["seoData"]["address"]["addressCountry"],
            "addr_full": ", ".join(
                filter(
                    None,
                    (
                        data["seoData"]["address"]["streetAddress"],
                        data["seoData"]["address"]["addressLocality"],
                        data["seoData"]["address"]["postalCode"],
                        data["seoData"]["address"]["addressCountry"],
                    ),
                )
            ),
            "website": response.request.url,
            "opening_hours": str(data["seoData"]["openingHours"])
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace(", ", "; "),
            "lat": geodata["store"]["latlng"]["lat"],
            "lon": geodata["store"]["latlng"]["lng"],
        }

        yield GeojsonPointItem(**properties)
