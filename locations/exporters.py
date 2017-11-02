from scrapy.exporters import JsonLinesItemExporter, JsonItemExporter
from scrapy.utils.python import to_bytes


class LineDelimitedGeoJsonExporter(JsonLinesItemExporter):

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(('type', 'Feature'))
        feature.append(('properties', item['properties']))

        if item.get('lon_lat'):
            feature.append(('geometry', {
                'type': 'Point',
                'coordinates': item['lon_lat'],
            }))

        return feature


class GeoJsonExporter(JsonItemExporter):

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(('type', 'Feature'))
        feature.append(('properties', item['properties']))

        if item.get('lon_lat'):
            feature.append(('geometry', {
                'type': 'Point',
                'coordinates': item['lon_lat'],
            }))

        return feature

    def start_exporting(self):
        self.file.write(to_bytes('{"type":"FeatureCollection","features":[', self.encoding))

    def finish_exporting(self):
        self.file.write(to_bytes(']}', self.encoding))
