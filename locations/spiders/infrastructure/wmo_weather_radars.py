from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature


class WmoWeatherRadarsSpider(Spider):
    name = "wmo_weather_radars"
    # Service hosted for the WMO by the Turkish State Meteorological Service (Q7855314)
    allowed_domains = ["wrd.mgm.gov.tr"]
    start_urls = ["https://wrd.mgm.gov.tr/Radar/All_Radars"]

    def parse(self, response: Response) -> Iterable[Request]:
        for radar in response.xpath('//table[@id="All_Radars"]/tbody/tr'):
            radar_website = radar.xpath('.//a[@class="nav-link"]/@href').get()
            yield Request(url=radar_website, callback=self.parse_radar_website)

    def parse_radar_website(self, response: Response) -> Iterable[Feature]:
        data_table = response.xpath('//div[@class="card-body"]/table[1]')
        properties = {
            "ref": data_table.xpath(".//tr[2]/td[2]/text()").get("").strip(),
            "name": data_table.xpath(".//tr[1]/td[2]/text()").get("").strip(),
            "lat": data_table.xpath(".//tr[5]/td[2]/text()").get("").strip(),
            "lon": data_table.xpath(".//tr[5]/td[4]/text()").get("").strip(),
            "operator": data_table.xpath(".//tr[3]/td[2]/text()").get("").strip(),
        }
        if not properties["lat"] or not properties["lon"]:
            # A small number of radars supplied without coordinates are mostly
            # blank records and of very little to no use. Ignore these few
            # radars to avoid errors relating to missing data.
            return
        if not properties["operator"]:
            # If no operator is listed, use the owner field instead.
            properties["operator"] = data_table.xpath(".//tr[7]/td[2]/text()").get("").strip()
        apply_category(Categories.MONITORING_STATION, properties)
        apply_category(Categories.ANTENNA, properties)
        properties["extras"]["tower:type"] = "radar"
        properties["extras"]["tower:construction"] = "dome"
        apply_yes_no(MonitoringTypes.WEATHER, properties, True)
        properties["extras"]["ref:wigos"] = properties["ref"]
        if country := data_table.xpath(".//tr[1]/td[4]/text()").get("").strip():
            properties["country"] = country.split(" - ", 1)[0]
        if elevation_m_str := data_table.xpath(".//tr[6]/td[2]/text()").get("").strip():
            elevation_m = round(float(elevation_m_str.removesuffix("m").strip()))
            if elevation_m > 0:
                properties["extras"]["ele"] = f"{elevation_m}"
        if height_m_str := data_table.xpath(".//tr[6]/td[4]/text()").get("").strip():
            height_m = round(float(height_m_str))
            if height_m > 0:
                properties["extras"]["height"] = f"{height_m}"
        if manufacturer := data_table.xpath(".//tr[7]/td[4]/text()").get("").strip():
            properties["extras"]["manufacturer"] = manufacturer
        if model := data_table.xpath(".//tr[13]/td[2]/text()").get("").strip():
            properties["extras"]["model"] = model
        if frequency_mhz_str := data_table.xpath(".//tr[10]/td[2]/text()").get("").strip():
            frequency_mhz = round(float(frequency_mhz_str))
            if frequency_mhz > 0:
                frequency_hz = frequency_mhz * 1000000
                properties["extras"]["frequency"] = f"{frequency_hz}"
        if power_kw_str := data_table.xpath(".//tr[11]/td[2]/text()").get("").strip():
            power_kw = round(float(power_kw_str))
            if power_kw > 0:
                properties["extras"]["rating"] = f"{power_kw} kW"
        if polarisation := data_table.xpath(".//tr[14]/td[2]/text()").get("").strip():
            match polarisation:
                case "D":
                    properties["extras"]["antenna:polarisation"] = "dual"
                case "S":
                    properties["extras"]["antenna:polarisation"] = "single"
                case _:
                    self.logger.warning(
                        "Unknown antenna polarisation '{}' for radar with WIGOS ID {}".format(
                            polarisation, properties["ref"]
                        )
                    )
        if start_date := data_table.xpath(".//tr[4]/td[2]/text()").get("").strip():
            properties["extras"]["start_date"] = start_date
        yield Feature(**properties)
