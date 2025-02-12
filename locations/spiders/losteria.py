import json
from urllib.parse import urlparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class LosteriaSpider(CrawlSpider, StructuredDataSpider):
    name = "losteria"
    item_attributes = {"brand": "L'Osteria", "brand_wikidata": "Q17323478"}
    countries = ["de", "at", "ch", "fr", "en", "nl", "cz", "lu", "pl"]
    start_urls = [
        f"https://losteria.net/en/restaurants/view/map/?tx_losteriarestaurants_restaurants%5Bfilter%5D%5Bcountry%5D={country}&tx_losteriarestaurants_restaurants%5Bfilter%5D%5BsearchTerm%5D=&tx_losteriarestaurants_restaurants%5Bfilter%5D%5Btype%5D=all&&&tx_losteriarestaurants_restaurants%5Bfilter%5D%5BmapView%5D=1"
        for country in countries
    ]
    sitemap_rules = [("/restaura(nts|ce)/restaurant/", "parse_sd")]
    rules = [
        Rule(LinkExtractor(allow=r"/restaurants/restaurant/"), callback="parse_sd"),
    ]
    country_url_map = {"gb": "en", "cz": "en"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        url = urlparse(response.url)
        path_components = url.path.split("/")
        item["ref"] = path_components[-2]
        coordinates_json = response.xpath("//div/@data-center").get()
        coordinates = json.loads(coordinates_json)
        item["lon"] = coordinates["lng"]
        item["lat"] = coordinates["lat"]
        # All restaurants are listed on all country websites, but we would like to get the country-specific URL
        country_code = item["country"]
        path_components[1] = self.country_url_map.get(country_code, country_code)
        item["website"] = url._replace(path="/".join(path_components), query=None, fragment=None).geturl()

        yield item
