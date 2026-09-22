import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

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


class IhWorldSpider(SitemapSpider):
    name = "ih_world"
    item_attributes = {
        "brand": "International House",
        "brand_wikidata": "Q6050993",
    }
    sitemap_urls = ["https://ihworld.com/sitemap_index.xml"]
    sitemap_follow = ["/schools-sitemap"]
    sitemap_rules = [(r"/schools/countries/[^/%]+/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.xpath("//body/@class").re_first(r"postid-(\d+)")
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("IH ")
        item["country"] = COUNTRY_MAP.get(
            response.xpath(
                '//nav[contains(@class, "rank-math-breadcrumb")]//a[contains(@href, "/schools/countries/")]/text()'
            ).get(""),
            "",
        )
        item["website"] = response.url

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
