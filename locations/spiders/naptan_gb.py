from scrapy import Spider

from locations.items import GeojsonPointItem


class NaptanGBSpider(Spider):
    name = "naptan_gb"
    start_urls = ["https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml"]

    def parse(self, response, **kwargs):
        response.selector.remove_namespaces()
        for point in response.xpath("/NaPTAN/StopPoints/StopPoint"):
            item = GeojsonPointItem()
            item["extras"] = {"check_date": point.xpath("@ModificationDateTime").get()}

            item["ref"] = item["extras"]["naptan:NaptanCode"] = point.xpath(
                "NaptanCode/text()"
            ).get()
            item["extras"]["naptan:AtcoCode"] = point.xpath("AtcoCode/text()").get()

            item["lat"] = point.xpath(
                "Place/Location/Translation/Latitude/text()"
            ).get()
            item["lon"] = point.xpath(
                "Place/Location/Translation/Longitude/text()"
            ).get()

            item["name"] = point.xpath("Descriptor/CommonName/text()").get()
            item["extras"]["short_name"] = point.xpath(
                "Descriptor/ShortCommonName/text()"
            ).get()
            item["extras"]["naptan:Landmark"] = point.xpath(
                "Descriptor/Landmark/text()"
            ).get()
            item["street"] = point.xpath("Descriptor/Street/text()").get()
            item["extras"]["naptan:Crossing"] = point.xpath(
                "Descriptor/Crossing/text()"
            ).get()
            item["extras"]["local_ref"] = point.xpath(
                "Descriptor/Indicator/text()"
            ).get()

            stop_type = point.xpath("StopClassification/StopType/text()").get()

            if stop_type == "BCT":  # Bus stop
                item["extras"]["public_transport"] = "platform"
                bus_stop_type = point.xpath(
                    "StopClassification/OnStreet/Bus/BusStopType/text()"
                ).get()

                if bus_stop_type == "MKD":
                    item["extras"]["direction"] = point.xpath(
                        "StopClassification/OnStreet/Bus/MarkedPoint/Bearing/CompassPoint/text()"
                    ).get()
                else:
                    item["extras"]["naptan:BusStopType"] = bus_stop_type
            elif stop_type == "BCS":  # Bus stop in bus station
                item["extras"]["public_transport"] = "stop_position"
                item["extras"]["bus"] = "yes"
            elif stop_type == "PLT":
                item["extras"]["railway"] = "tram_stop"
            elif stop_type in ["TXR", "STR"]:  # Taxis
                item["extras"]["amenity"] = "taxi"
            elif stop_type in ["RSE", "FTD", "BCE", "TMU", "AIR"]:  # Station entrances
                item["extras"]["entrance"] = "yes"
            elif stop_type in ["MET", "BST"]:  # "access area"
                continue
            else:
                item["extras"]["stop_type"] = stop_type

            yield item

        for point in response.xpath("/NaPTAN/StopAreas/StopArea"):
            item = GeojsonPointItem()
            item["extras"] = {"check_date": point.xpath("@ModificationDateTime").get()}

            item["ref"] = point.xpath("StopAreaCode/text()").get()

            item["lat"] = point.xpath("Location/Translation/Latitude/text()").get()
            item["lon"] = point.xpath("Location/Translation/Longitude/text()").get()

            item["name"] = point.xpath("Name/text()").get()

            stop_type = point.xpath("StopAreaType/text()").get()

            if stop_type == "GBCS":  # Bus station
                item["extras"]["public_transport"] = "station"
            elif stop_type in ["GPBS", "GCLS", "GCCH"]:  # Collection of stops
                item["extras"]["public_transport"] = "stop_area"
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
