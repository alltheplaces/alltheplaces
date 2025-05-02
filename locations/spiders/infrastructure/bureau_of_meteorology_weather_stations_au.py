from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.archive_utils import unzip_file_from_archive
from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature


class BureauOfMeteorologyWeatherStationsAUSpider(Spider):
    name = "bureau_of_meteorology_weather_stations_au"
    item_attributes = {"operator": "Bureau of Meteorology", "operator_wikidata": "Q923429"}
    start_urls = ["ftp://ftp.bom.gov.au/anon2/home/ncc/metadata/sitelists/stations.zip"]
    skip_auto_cc = True  # Too coarse/Inaccurate polygons confuse outlying Australian islands/territories
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Scrapy always ignores FTP URLs unless ROBOTSTXT_OBEY=False

    def start_requests(self) -> Iterable[Request]:
        yield Request(url=self.start_urls[0], meta={"ftp_user": "anonymous", "ftp_password": ""})

    def parse(self, response: Response) -> Iterable[Feature]:
        station_data = unzip_file_from_archive(response.body, "stations.txt").decode("ascii").splitlines()[4:-6]

        for station in station_data:
            site_id = station[1:8].strip()
            site_name = station[14:55].strip()
            start_date = station[58:63].strip()
            end_date = station[66:71].strip()
            lat = float(station[71:80].strip())
            lon = float(station[81:90].strip())
            altitude = station[113:120].strip()
            wmo_id = station[130:136].strip()

            properties = {
                "ref": site_id,
                "name": site_name,
                "lat": lat,
                "lon": lon,
                "website": "http://www.bom.gov.au/climate/averages/tables/cw_{}.shtml".format(site_id),
                "extras": {
                    "start_date": start_date,
                    "website:map": "http://www.bom.gov.au/clim_data/cdio/metadata/pdf/siteinfo/IDCJMD0040.{}.SiteInfo.pdf".format(
                        site_id
                    ),
                },
            }

            if end_date != "..":
                properties["extras"]["removed:man_made"] = "monitoring_station"
                properties["extras"]["removed:monitoring_station"] = "weather"
                properties["extras"]["end_date"] = end_date
                properties["nsi_id"] = "N/A"
            else:
                apply_category(Categories.MONITORING_STATION, properties)
                apply_yes_no(MonitoringTypes.WEATHER, properties, True)

            if altitude != "..":
                properties["extras"]["ele"] = altitude
            if wmo_id != "..":
                properties["extras"]["ref:wmo"] = wmo_id

            yield Feature(**properties)
