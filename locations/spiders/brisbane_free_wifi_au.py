from hashlib import sha1

from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class BrisbaneFreeWiFiAUSpider(XMLFeedSpider):
    name = "brisbane_free_wifi_au"
    item_attributes = {"operator": "Brisbane City Council", "operator_wikidata": "Q56477660"}
    allowed_domains = ["www.brisbane.qld.gov.au"]
    start_urls = ["https://www.brisbane.qld.gov.au/maps/layers/kml/16"]
    iterator = "xml"
    itertag = "Placemark"

    def parse_node(self, response, node):
        properties = {
            "ref": sha1(node.xpath(".//Point/coordinates/text()").get().encode("UTF-8")).hexdigest(),
            "name": node.xpath(".//name/text()").get(),
            "lat": node.xpath(".//Point/coordinates/text()").get().split(",", 3)[1],
            "lon": node.xpath(".//Point/coordinates/text()").get().split(",", 3)[0],
            "city": node.xpath('.//ExtendedData/Data[@name="suburb"]/value/text()').get(),
            "extras": {
                "internet_access": "wlan",
                "internet_access:fee": "no",
                "internet_access:operator": "Telstra",
                "internet_access:operator:wikidata": "Q721162",
                "internet_access:ssid": "Brisbane Free Wi-Fi",
            },
        }
        apply_category(Categories.ANTENNA, properties)
        yield Feature(**properties)
