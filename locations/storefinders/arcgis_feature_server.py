from datetime import UTC, datetime, timedelta
from typing import Iterable
from urllib.parse import quote_plus

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class ArcGISFeatureServerSpider(Spider):
    """
    Official documentation of the ArcGIS Feature Server query API:
    https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/

    To use this store finder, specify a `host`, a `context_path`, a
    `service_id` and a `layer_id`. If the server type is `MapServer` instead
    of the default `FeatureServer`, optionally set `server_type` to be
    `MapServer`. Optionally specify `field_names` if it is  beneficial to only
    work with a subset of all fields available within the layer. These
    attributes can be extracted from URLs as follows:
      https://{host}/{context_path}/rest/services/{service_id}/{server_type}/{layer_id}

    Example:
        URL: https://services.arcgis.com/1234567890abcdef/ArcGIS/rest/services/Sample/FeatureServer/0

        Properties:
        `host`: services.arcgis.com
        `context_path`: 1234567890abcdef/ArcGIS
        `service_id`: Sample
        `server_type`: FeatureServer
        `layer_id`: 0

    It is also possible to filter features using the attribute `where_query`.
    This is a SQL-like syntax, with some examples being:
      * `where_query = "FEATURE_TYPE <> 'TOILET'"`
      * `where_query = "FEATURE_TYPE = 'PARK'"`
      * `where_query = "FEATURE_TYPE <> 'Unknown' AND OPEN_STATUS = 'OPEN'"`

    In some rare cases, it may be necessary to add additional parameters to
    each query of the ArcGIS server. An example is the parameter
    "&token=12345". To specify such parameter(s), set a list of additional
    parameters using the key/value dictionary attribute of this class,
    `additional_parameters`.

    Each feature within the specified layer is run through `DictParser.parse`
    to try and automatically extract as much information as possible. Override
    the `pre_process_data` function to modify field values before
    `DictParser.parse` is called. Override the `post_process_item` function to
    extract additional information from the source feature or to clean data
    after automatic extraction has been attempted.

    Different ArcGIS Feature Servers will have varied maximum record counts
    configured to be returned per query. This class will automatically detect
    the maximum record counts and request all features, batch by batch.

    Warnings will raised if any of the following conditions occur:
      1. Source data has a last data modification timestamp greater than 365
         days ago. This warning is a prompt to double check the latest source
         data is in use and that the brand/operator hasn't changed systems for
         publishing geographic information about features.
      2. A field defined in the `field_names` attribute is not present in the
         requested layer. This may indicate the data publisher has changed the
         schema of the feature layer to omit, rename or replace a field.
    """

    dataset_attributes = {"source": "api", "api": "arcgis"}

    host: str = ""
    context_path: str = ""
    service_id: str = ""
    server_type: str = "FeatureServer"  # Or "MapServer"
    layer_id: str = ""
    field_names: list[str] = []
    where_query: str = "1=1"
    additional_parameters: dict = {}

    # robots.txt does not exist and instead returns a HTTP 404 page which
    # triggers a number of Scrapy warning messages.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        layer_details_url = f"https://{self.host}/{self.context_path}/rest/services/{self.service_id}/{self.server_type}/{self.layer_id}?f=json"
        if len(self.additional_parameters.keys()) > 0:
            additional_parameters_str = "".join([f"&{parameter_name}={parameter_value}" for parameter_name, parameter_value in self.additional_parameters.items()])
            layer_details_url = layer_details_url + additional_parameters_str
        yield JsonRequest(url=layer_details_url, callback=self.parse_layer_details)

    def parse_layer_details(self, response: Response) -> Iterable[JsonRequest]:
        layer_details = response.json()

        server_capabilities = list(map(str.strip, layer_details["capabilities"].split(",")))
        if "Query" not in server_capabilities:
            raise RuntimeError(
                "ArcGIS Feature Server does not support a query method which ArcGISFeatureServerSpider expects."
            )

        query_formats = list(map(str.strip, layer_details["supportedQueryFormats"].split(",")))
        if "geoJSON" not in query_formats:
            raise RuntimeError(
                "ArcGIS Feature Server does not support GeoJSON output which ArcGISFeatureServerSpider expects."
            )

        if (
            layer_details.get("dateFieldsTimeReference")
            and layer_details["dateFieldsTimeReference"].get("timeZone") == "UTC"
            and layer_details.get("editingInfo")
            and layer_details["editingInfo"].get("dataLastEditDate")
        ):
            timestamp_of_last_edit = datetime.fromtimestamp(
                int(float(layer_details["editingInfo"]["dataLastEditDate"]) / 1000), UTC
            )
            self.dataset_attributes.update({"source:date": timestamp_of_last_edit.isoformat()})
            current_timestamp = datetime.now(UTC)
            if current_timestamp - timestamp_of_last_edit > timedelta(days=365):
                self.logger.warning(
                    "The requested layer is possibly outdated as layer data was last edited over 365 days ago on {}.".format(
                        timestamp_of_last_edit.isoformat()
                    )
                )
        elif layer_details.get("editingInfo") and layer_details["editingInfo"].get("dataLastEditDate"):
            self.logger.warning(
                "Cannot extract date of last data edit for specified layer due to use of non-UTC timezone which ArcGISFeatureServerSpider doesn't currently support."
            )

        output_fields = "*"
        if len(self.field_names) > 1:
            available_field_names = [available_field["name"] for available_field in layer_details["fields"]]
            output_field_names = []
            for field_name in self.field_names:
                if field_name not in available_field_names:
                    self.logger.warning(
                        "Spider requested that field `{}` be extracted for each feature in the layer but the layer doesn't have a field named `{}`. Field ignored.".format(
                            field_name, field_name
                        )
                    )
                    continue
                output_field_names.append(field_name)
            output_fields = ",".join(output_field_names)

        max_record_count_fields = ""
        if max_record_count := layer_details["maxRecordCount"]:
            max_record_count_fields = f"&resultOffset=0&resultRecordCount={max_record_count}"

        where_query_urlencoded = quote_plus(self.where_query)

        query_url = f"https://{self.host}/{self.context_path}/rest/services/{self.service_id}/{self.server_type}/{self.layer_id}/query?where={where_query_urlencoded}&outFields={output_fields}&outSR=4326{max_record_count_fields}&f=geojson"
        if len(self.additional_parameters.keys()) > 0:
            additional_parameters_str = "".join([f"&{parameter_name}={parameter_value}" for parameter_name, parameter_value in self.additional_parameters.items()])
            query_url = query_url + additional_parameters_str
        yield JsonRequest(url=query_url, callback=self.parse_features)

    def parse_features(self, response: Response) -> Iterable[Feature]:
        features = response.json()["features"]

        for feature in features:
            properties = feature.pop("properties")
            if "geometry" in properties.keys():
                # Prevent unlikely (but still possible) overwriting of feature
                # geometry if GeoJSON properties include a "geometry" field.
                properties["__geometry"] = properties.pop("geometry")
            feature.update(properties)
            self.pre_process_data(feature)
            item = DictParser.parse(feature)

            # Esri's GeoJSON output is not always valid, so check for known problems
            geom = item.get("geometry")
            if geom and geom.get("coordinates") == []:
                item["geometry"] = None

            yield from self.post_process_item(item, response, feature)

        if "&resultRecordCount=" in response.url:
            max_record_count = int(response.request.url.split("&resultRecordCount=", 1)[1].split("&", 1)[0])
            if len(features) == max_record_count:
                # More results exist and need to be queried for.
                current_offset = int(response.request.url.split("&resultOffset=", 1)[1].split("&", 1)[0])
                next_offset = current_offset + max_record_count
                yield JsonRequest(
                    url=response.request.url.replace(f"&resultOffset={current_offset}", f"&resultOffset={next_offset}"),
                    callback=self.parse_features,
                    dont_filter=True,
                )

    def pre_process_data(self, feature: dict) -> None:
        return

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        yield item
