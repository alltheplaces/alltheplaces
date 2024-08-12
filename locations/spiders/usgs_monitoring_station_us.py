from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature


class UsgsMonitoringStationUSSpider(Spider):
    name = "usgs_monitoring_station_us"
    item_attributes = {"operator": "United States Geological Survey", "operator_wikidata": "Q193755"}
    start_urls = [
        "https://dashboard.waterdata.usgs.gov/service/cwis/1.0/odata/CurrentConditions?$top=15000&$filter=(AccessLevelCode%20eq%20%27P%27)%20and%20(SiteTypeCode%20%20in%20(%27ST%27%2C%27ST-CA%27%2C%27ST-DCH%27%2C%27ST-TS%27))%20and%20(ParameterCode%20in%20(%2730208%27%2C%2730209%27%2C%2750042%27%2C%2750050%27%2C%2750051%27%2C%2772137%27%2C%2772138%27%2C%2772139%27%2C%2772177%27%2C%2772243%27%2C%2774072%27%2C%2781395%27%2C%2799060%27%2C%2799061%27%2C%2700056%27%2C%2700058%27%2C%2700059%27%2C%2700060%27%2C%2700061%27))&$select=AgencyCode,SiteNumber,SiteName,SiteTypeCode,Latitude,Longitude,CurrentConditionID,ParameterCode,TimeLocal,TimeZoneCode,Value,ValueFlagCode,RateOfChangeUnitPerHour,StatisticStatusCode,FloodStageStatusCode&$orderby=SiteNumber,AgencyCode,ParameterCode,TimeLocal%20desc&caller=National%20Water%20Dashboard%20default"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["value"]:
            item = Feature()
            item["ref"] = location["SiteNumber"]
            item["name"] = location["SiteName"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            item["website"] = "https://waterdata.usgs.gov/monitoring-location/{}/".format(location["SiteNumber"])
            item["extras"]["SiteTypeCode"] = location["SiteTypeCode"]

            apply_category({"man_made": "monitoring_station"}, item)

            yield item
