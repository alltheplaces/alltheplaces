# -*- coding: utf-8 -*-
import scrapy
import json
import html
from locations.dict_parser import DictParser


def from_wikidata(name, code):
    return {"brand": name, "brand_wikidata": code}


def set_brand(item, brand):
    item["brand"] = brand.get("brand")
    item["brand_wikidata"] = brand.get("brand_wikidata")


class BestWesternSpider(scrapy.spiders.SitemapSpider):
    name = "bestwestern"
    brands = [
        from_wikidata("Best Western Premier", "Q830334"),
        from_wikidata("Best Western Plus", "Q830334"),
        from_wikidata("Aiden by Best Western", "Q830334"),
        from_wikidata("Sure Hotel", "Q830334"),
        from_wikidata("Surestay Plus", "Q830334"),
        from_wikidata("Surestay", "Q830334"),
        from_wikidata("Best Western", "Q830334"),
    ]
    allowed_domains = ["bestwestern.com"]
    sitemap_urls = ["https://www.bestwestern.com/etc/seo/bestwestern/hotels.xml"]
    sitemap_rules = [(r"/en_US/book/hotels-in-.*\.html", "parse_hotel")]
    download_delay = 0.5

    def parse_hotel(self, response):
        data_hotel_details = response.xpath(
            '//div[@id="hotel-details-info"]/@data-hoteldetails'
        ).get()
        if data_hotel_details:
            json_data = json.loads(html.unescape(data_hotel_details))
            summary = json_data["summary"]
            my_name = summary["name"].lower()
            my_brand = None
            for brand in self.brands:
                if my_name.startswith(brand["brand"].lower()):
                    my_brand = brand
                    break
            if not my_brand:
                # For the most part these are hotels not owned by BW, but part of a "collection"
                return
            item = DictParser.parse(summary)
            set_brand(item, my_brand)
            hotel_code = summary["resort"]
            item["website"] = response.url
            item["ref"] = hotel_code
            try:
                # It's a big hotel chain, worth a bit of work to get the imagery.
                image_path = json_data["imageCatalog"]["Media"][0]["ImagePath"]
                item[
                    "image"
                ] = "https://images.bestwestern.com/bwi/brochures/{}/photos/1024/{}".format(
                    hotel_code, image_path
                )
            except IndexError:
                pass
            item["street_address"] = summary["address1"]
            return item
