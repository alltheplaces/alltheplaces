from scrapy.spiders import XMLFeedSpider

from locations.hours import OpeningHours
from locations.items import Feature


class ChemistWarehouseAUSpider(XMLFeedSpider):
    name = "chemist_warehouse_au"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}
    allowed_domains = ["www.chemistwarehouse.com.au"]
    start_urls = [
        "https://www.chemistwarehouse.com.au/ams/webparts/Google_Map_SL_files/storelocator_data.ashx?searchedPoint=(0,%200)&TrafficSource=1&TrafficSourceState=0"
    ]
    requires_proxy = True  # Residential IP addresses appear to be required.
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response, node):
        properties = {
            "ref": node.xpath("@id").get(),
            "name": node.xpath("@storename").get(),
            "lat": node.xpath("@lat").get(),
            "lon": node.xpath("@lon").get(),
            "street_address": node.xpath("@storeaddress").get(),
            "city": node.xpath("@storesuburb").get(),
            "state": node.xpath("@storestate").get(),
            "postcode": node.xpath("@storepostcode").get(),
            "phone": node.xpath("@storephone").get(),
            "email": node.xpath("@storeemail").get(),
        }
        hours_string = " ".join(
            [
                "Mon: ",
                node.xpath("@storemon").get(),
                "Tue: ",
                node.xpath("@storetue").get(),
                "Wed: ",
                node.xpath("@storewed").get(),
                "Thu: ",
                node.xpath("@storethu").get(),
                "Fri: ",
                node.xpath("@storefri").get(),
                "Sat: ",
                node.xpath("@storesat").get(),
                "Sun: ",
                node.xpath("@storesun").get(),
            ]
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
