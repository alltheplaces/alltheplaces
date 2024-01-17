from scrapy.spiders import XMLFeedSpider

from locations.hours import OpeningHours
from locations.items import Feature


class ChemistWarehouseAUSpider(XMLFeedSpider):
    name = "chemist_warehouse_au"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}
    allowed_domains = ["www.chemistwarehouse.com.au"]
    start_urls = [
        "https://www.chemistwarehouse.com.au/webapi/store/store-locator?BusinessGroupId=2&SortByDistance=true&SearchByState=0&Coordinate=(-37.8152065,%20144.963937)&ShowNearbyOnly=false"
    ]
    requires_proxy = True  # Residential IP addresses appear to be required.
    iterator = "xml"
    namespaces = [("cw", "http://schemas.datacontract.org/2004/07/AmSolutions.ChemistWarehouse.Models.Store")]
    itertag = "cw:StoreLocationModel"

    def parse_node(self, response, node):
        properties = {
            "ref": node.xpath("cw:Id/text()").get(),
            "name": node.xpath("cw:Name/text()").get(),
            "lat": node.xpath("cw:GeoPoint/cw:Latitude/text()").get(),
            "lon": node.xpath("cw:GeoPoint/cw:Longitude/text()").get(),
            "street_address": node.xpath("cw:Address/text()").get(),
            "city": node.xpath("cw:Suburb/text()").get(),
            "state": node.xpath("cw:State/text()").get(),
            "postcode": node.xpath("cw:Postcode/text()").get(),
            "phone": node.xpath("cw:Phone/text()").get(),
            "email": node.xpath("cw:Email/text()").get(),
        }
        properties["opening_hours"] = OpeningHours()
        for day_hours in node.xpath("cw:OpenHours/cw:OpenHour"):
            properties["opening_hours"].add_range(
                day_hours.xpath("cw:WeekDay/text()").get(),
                day_hours.xpath("cw:OpenTime/text()").get(),
                day_hours.xpath("cw:CloseTime/text()").get(),
                "%I:%M %p",
            )
        yield Feature(**properties)
