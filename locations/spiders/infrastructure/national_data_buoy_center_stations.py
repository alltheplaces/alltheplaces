from typing import Iterable

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature


class NationalDataBuoyCenterStationsSpider(XMLFeedSpider):
    name = "national_data_buoy_center_stations"
    allowed_domains = ["www.ndbc.noaa.gov"]
    start_urls = ["https://www.ndbc.noaa.gov/activestations.xml"]
    iterator = "xml"
    itertag = "station"
    # Skip reverse geocoding because most buoys are in international waters
    # or the reverse geocoder doesn't know where territorial borders exist.
    skip_auto_cc_geocoder = True
    skip_auto_cc_domain = True

    def parse_node(self, response: Response, node: Selector) -> Iterable[Feature]:
        # The format of the XML document is described at:
        # https://www.ndbc.noaa.gov/docs/ndbc_web_data_guide.pdf
        properties = {
            "ref": node.xpath("./@id").get(),
            "name": node.xpath("./@name").get(),
            "lat": node.xpath("./@lat").get(),
            "lon": node.xpath("./@lon").get(),
            "operator": node.xpath("./@owner").get(),
        }
        station_type = node.xpath("./@type").get()
        match station_type:
            case "buoy" | "dart":
                apply_category(Categories.MONITORING_STATION, properties)
                properties["extras"]["seamark:type"] = "buoy_special_purpose"
                properties["extras"]["seamark:buoy_special_purpose:category"] = "recording"
            case "fixed":
                apply_category(Categories.MONITORING_STATION, properties)
            case _:
                self.logger.warning("Unknown station type: {}. Feature ignored.".format(station_type))
                return
        # Note: for monitoring types, the source data only indicates "y" for a
        # station that has reported a type of monitoring data in the last 8
        # hours, or 24 hours for "dart" (column height/tsunami data). A
        # station temporarily out of service for repair/maintenance will
        # report no monitoring types, even if the station is capable of and
        # intended to monitor. Each run of this spider may therefore generate
        # different results depending on very current (last 8 hours)
        # observation of what a station is currently monitoring.
        apply_yes_no(MonitoringTypes.WEATHER, properties, node.xpath("./@met").get() == "y")
        # There doesn't appear to be any current monitoring type used by OSM
        # for ocean currents, so the below is made up.
        apply_yes_no("monitoring:ocean_current", properties, node.xpath("./@currents").get() == "y")
        apply_yes_no(MonitoringTypes.WATER_QUALITY, properties, node.xpath("./@waterquality").get() == "y")
        # monitoring:tsunami is not a documented OSM monitoring type and has
        # very limited use at present. This seems to be closest match to what
        # the source data intends by "DART" monitoring. For more on DART refer
        # to https://www.ndbc.noaa.gov/dart/dart.shtml
        apply_yes_no("monitoring:tsunami", properties, node.xpath("./@dart").get() == "y")
        yield Feature(**properties)
