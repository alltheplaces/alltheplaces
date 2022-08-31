# -*- coding: utf-8 -*-
import scrapy
import json
import html
from locations.dict_parser import DictParser


def from_wikidata(name, code):
    return {"brand": name, "brand_wikidata": code}


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
        hotel_details = response.xpath(
            '//div[@id="hotel-details-info"]/@data-hoteldetails'
        ).get()
        if hotel_details:
            hotel = json.loads(html.unescape(hotel_details))
            summary = hotel["summary"]
            for brand in self.brands:
                if summary["name"].lower().startswith(brand["brand"].lower()):
                    item = DictParser.parse(summary)
                    item.update(brand)
                    item["street_address"] = summary["address1"]
                    item["website"] = response.url
                    item["ref"] = summary["resort"]
                    try:
                        # It's a big hotel chain, worth a bit of work to get the imagery.
                        image_path = hotel["imageCatalog"]["Media"][0]["ImagePath"]
                        item[
                            "image"
                        ] = "https://images.bestwestern.com/bwi/brochures/{}/photos/1024/{}".format(
                            summary["resort"], image_path
                        )
                    except IndexError:
                        pass
                    yield item
                    return
