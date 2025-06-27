from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature


class FdsnSeismicStationsSpider(Spider):
    name = "fdsn_seismic_stations"
    start_urls = ["https://www.fdsn.org/ws/datacenters/1/query"]
    # Some FDSN registered "datacenters" (respositories) will result in DNS
    # timeouts or other failures. Don't retry failed requests because it's
    # probably not going to help.
    # The largest "datacenter" is service.iris.edu which takes a few minutes
    # to prepare and download a full list of stations. The total size of the
    # XML document returned is over 32MiB but less then 64MiB.
    custom_settings = {"RETRY_ENABLED": False, "DOWNLOAD_TIMEOUT": 180, "DOWNLOAD_WARNSIZE": 67108864}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], callback=self.parse_datacenters)

    def parse_datacenters(self, response: Response) -> Iterable[JsonRequest]:
        for datacenter in response.json()["datacenters"]:
            for repository in datacenter["repositories"]:
                for service in repository["services"]:
                    if service["name"] == "fdsnws-station-1":
                        station_list_url = service["url"]
                        if station_list_url.endswith("/"):
                            station_list_url = f"{station_list_url}query"
                        else:
                            station_list_url = f"{station_list_url}/query"
                        yield Request(url=station_list_url, callback=self.parse_station_list)

    def parse_station_list(self, response: Response) -> Iterable[Feature]:
        document = Selector(response=response, type="xml")
        document.register_namespace("s", "http://www.fdsn.org/xml/station/1")
        for network in document.xpath("//s:Network"):
            for station in network.xpath("./s:Station"):
                if station.xpath("./@endDate").get():
                    # Station has an end date and therefore no longer exists.
                    # Ignore historical stations.
                    continue
                properties = {
                    "ref": network.xpath("./@code").get() + "-" + station.xpath("./@code").get(),
                    "name": station.xpath("./s:Site/s:Name/text()").get(),
                    "lat": station.xpath("./s:Latitude/text()").get(),
                    "lon": station.xpath("./s:Longitude/text()").get(),
                }
                if end_date := station.xpath("./@endDate").get():
                    # Station has an end date and therefore has been shutdown/
                    # removed. Extract the point as a historical feature as
                    # there is historical data at this location which
                    # continues to be a feature of interest.
                    properties["extras"]["removed:man_made"] = "monitoring_station"
                    properties["extras"]["removed:monitoring_station"] = "seismic_activity"
                    properties["extras"]["end_date"] = station.xpath("./@endDate").get().split("T", 1)[0]
                else:
                    # Station has no end date and therefore is active and
                    # continues to exist.
                    apply_category(Categories.MONITORING_STATION, properties)
                    apply_yes_no(MonitoringTypes.SEISMIC_ACTIVITY, properties, True)
                properties["extras"]["ref:fdsn:network"] = network.xpath("./@code").get()
                properties["extras"]["ref:fdsn:station"] = station.xpath("./@code").get()
                if elevation_m := station.xpath("./s:Elevation/text()").get():
                    properties["extras"]["ele"] = elevation_m
                if start_date := station.xpath("./@startDate").get():
                    properties["extras"]["start_date"] = start_date.split("T", 1)[0]
                yield Feature(**properties)
