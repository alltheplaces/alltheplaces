from typing import Any

from scrapy import Request, Spider
from scrapy.http import XmlResponse

from locations.items import Feature


class NaptanGBSpider(Spider):
    name = "naptan_gb"
    start_urls = ["https://naptan.api.dft.gov.uk/v1/nptg"]

    def parse(self, response: XmlResponse, **kwargs: Any) -> Any:
        response.selector.register_namespace("n", "http://www.naptan.org.uk/")

        for area in response.xpath(
            "/n:NationalPublicTransportGazetteer/n:Regions/n:Region/n:AdministrativeAreas/n:AdministrativeArea"
        ):
            yield Request(
                "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml&atcoAreaCodes={}".format(
                    area.xpath("./n:AtcoAreaCode/text()").get()
                ),
                callback=self.parse_nodes,
            )

    def parse_nodes(self, response: XmlResponse, **kwargs: Any) -> Any:
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
