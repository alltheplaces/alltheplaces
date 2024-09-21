import json

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BjRestaurantSpider(SitemapSpider):
    name = "bj_restaurant"
    item_attributes = {
        "brand": "BJ's Restaurant & Brewery",
        "brand_wikidata": "Q4835755",
    }
    sitemap_urls = ("https://www.bjsrestaurants.com/sitemap.xml",)
    sitemap_rules = [
        (
            r"https://www.bjsrestaurants.com/locations/\w\w/\w+",
            "parse",
        )
    ]

    def parse(self, response):
        f = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first())
        restaurant_data = f["props"]["pageProps"]["model"][":items"]["root"][":items"]["responsivegrid"][":items"][
            "restaurantdetails"
        ]["restaurant"]
        nested_json = json.loads(
            restaurant_data["seoScript"]
        )
        item = LinkedDataParser.parse_ld(nested_json, time_format="%H:%M:%S"))
        item["ref"] = restaurant_data["restaurantId"]
        yield item
