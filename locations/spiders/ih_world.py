import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

COUNTRY_MAP = {
    "Angola": "AO",
    "Argentina": "AR",
    "Bulgaria": "BG",
    "Canada": "CA",
    "Chile": "CL",
    "Colombia": "CO",
    "Croatia": "HR",
    "Czech Republic": "CZ",
    "Ecuador": "EC",
    "Egypt": "EG",
    "Estonia": "EE",
    "France": "FR",
    "Georgia": "GE",
    "Germany": "DE",
    "Hungary": "HU",
    "Ireland": "IE",
    "Italy": "IT",
    "Jordan": "JO",
    "Kazakhstan": "KZ",
    "Laos": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Libya": "LY",
    "Malta": "MT",
    "Mexico": "MX",
    "Montenegro": "ME",
    "Myanmar": "MM",
    "Pakistan": "PK",
    "Peru": "PE",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Russia": "RU",
    "Saudi Arabia": "SA",
    "Serbia": "RS",
    "Slovakia": "SK",
    "South Africa": "ZA",
    "Spain": "ES",
    "Thailand": "TH",
    "Turkey": "TR",
    "Ukraine": "UA",
    "United Kingdom": "GB",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Vietnam": "VN",
}


class IhWorldSpider(Spider):
    name = "ih_world"
    item_attributes = {
        "brand": "International House",
        "brand_wikidata": "Q6050993",
    }
    start_urls = [
        "https://ihworld.com/wp-json/wp/v2/schools?per_page=100&page=1&_embed",
        "https://ihworld.com/wp-json/wp/v2/schools?per_page=100&page=2&_embed",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Iterable:
        for school in response.json():
            country_name = ""
            for termlist in school.get("_embedded", {}).get("wp:term", []):
                for term in termlist:
                    if term.get("taxonomy") == "countries":
                        country_name = term.get("name", "")
                        break

            yield response.follow(
                school["link"],
                callback=self.parse_school,
                cb_kwargs={
                    "ref": str(school["id"]),
                    "name": school["title"]["rendered"],
                    "country": COUNTRY_MAP.get(country_name, ""),
                    "website_url": school["link"],
                },
            )

    def parse_school(
        self,
        response: Response,
        ref: str,
        name: str,
        country: str,
        website_url: str,
        **kwargs: Any,
    ) -> Iterable:
        item = Feature()
        item["ref"] = ref
        item["name"] = name
        item["country"] = country
        item["website"] = website_url

        # Extract address from Google Maps embed query parameter
        maps_q = response.xpath(
            '//iframe[contains(@src,"maps.google.com")]/@src | //a[contains(@href,"maps.google.com/maps?q=")]/@href'
        ).get()
        if maps_q:
            match = re.search(r"maps\.google\.com/maps\?q=([^&\"' ]+)", maps_q)
            if match:
                item["addr_full"] = unquote(match.group(1))
        if not item.get("addr_full"):
            # Try generic google maps embed via src= in elementor widget
            src_maps = re.search(
                r'google\.com/maps\?q=([^&"\'\\s]+)',
                response.text,
            )
            if src_maps:
                item["addr_full"] = unquote(src_maps.group(1))

        # Phone: prefer tel: links
        phones = response.xpath('//a[starts-with(@href,"tel:")]/@href').getall()
        if phones:
            item["phone"] = phones[0].replace("tel:", "").strip()

        # Email: prefer mailto: links
        emails = response.xpath('//a[starts-with(@href,"mailto:")]/@href').getall()
        if emails:
            item["email"] = emails[0].replace("mailto:", "").strip()

        apply_category(Categories.LANGUAGE_SCHOOL, item)
        yield item
