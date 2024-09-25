from scrapy import Spider

from locations.items import Feature


class NaptanGBSpider(Spider):
    name = "naptan_gb"
    # Smaller areas can be tested: eg "&atcoAreaCodes=010"
    start_urls = ["https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml"]
    requires_proxy = True
    
    def parse(self, response, **kwargs):
        response.selector.remove_namespaces()

        for point in response.xpath("/NaPTAN/StopAreas/StopArea"):
            if point.xpath("@Status").get() != "active":
                continue

            item = Feature()
            item["extras"] = {"check_date": point.xpath("@ModificationDateTime").get()}

            item["ref"] = item["extras"]["naptan:AtcoCode"] = point.xpath("StopAreaCode/text()").get()

            item["lat"] = point.xpath("Location/Translation/Latitude/text()").get()
            item["lon"] = point.xpath("Location/Translation/Longitude/text()").get()

            item["name"] = point.xpath("Name/text()").get()

            stop_type = point.xpath("StopAreaType/text()").get()

            if stop_type == "GBCS":  # Bus station
                item["extras"]["public_transport"] = "station"
                item["extras"]["amenity"] = "bus_station"
            elif stop_type in ["GPBS", "GCLS", "GCCH"]:  # Collection of stops
                item["extras"]["public_transport"] = "stop_area"
                continue
            elif stop_type == "GAIR":  # Airport
                item["extras"]["aeroway"] = "aerodrome"
            elif stop_type == "GFTD":  # Ferry Terminal
                item["extras"]["amenity"] = "ferry_terminal"
            elif stop_type == "GTMU":  # Tram
                item["extras"]["public_transport"] = "platform"
                item["extras"]["railway"] = "platform"
            elif stop_type == "GRLS":  # Train station
                item["extras"]["public_transport"] = "platform"
                item["extras"]["railway"] = "platform"
            else:
                item["extras"]["stop_type"] = stop_type

            yield item
