from scrapy import Selector
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser, get_object


# Malformed Microdata
# root itemscope also an itemprop=brand
def extract_microdata(doc: Selector):
    result = {}
    items = []
    for item in doc.xpath('//*[@itemscope][not(@itemprop) or @itemprop="brand"]'):
        items.append(get_object(item.root))

    result["items"] = items

    return result


class WimpyGBSpider(SitemapSpider):
    name = "wimpy_gb"
    item_attributes = {"brand": "Wimpy", "brand_wikidata": "Q2811992"}
    sitemap_urls = ["https://locations.wimpy.uk.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.wimpy\.uk\.com/[^/]+/[^/]+/[^/]+/[^/]+\.html", "parse")]

    def parse(self, response, **kwargs):
        for ld in MicrodataParser.convert_to_graph(extract_microdata(response))["@graph"]:
            if ld["@type"] == "FastFoodRestaurant":
                item = LinkedDataParser.parse_ld(ld)
                item["ref"] = response.url
                item["image"] = None
                item["branch"] = item.pop("name").removeprefix("Wimpy ")
                item["country"] = "GB"

                yield item
