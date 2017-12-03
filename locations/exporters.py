from scrapy.exporters import JsonLinesItemExporter, JsonItemExporter
from scrapy.utils.python import to_bytes


mapping = (
    ('addr_full', 'addr:full'),
    ('housenumber', 'addr:housenumber'),
    ('street', 'addr:street'),
    ('city', 'addr:city'),
    ('state', 'addr:state'),
    ('postcode', 'addr:postcode'),
    ('country', 'addr:country'),
    ('name', 'name'),
    ('phone', 'phone'),
    ('website', 'website'),
    ('opening_hours', 'opening_hours'),
)


def item_to_properties(item):
    props = {}

    # Ref is required
    props['ref'] = item['ref']

    # Add in the extra bits
    extras = item.get('extras')
    if extras:
        props.update(extras)

    # Bring in the optional stuff
    for map_from, map_to in mapping:
        item_value = item.get(map_from)
        if item_value:
            props[map_to] = item_value

    return props


class LineDelimitedGeoJsonExporter(JsonLinesItemExporter):

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(('type', 'Feature'))
        feature.append(('properties', item_to_properties(item)))

        if item.get('lon'):
            feature.append(('geometry', {
                'type': 'Point',
                'coordinates': [
                    item['lon'],
                    item['lat']
                ],
            }))

        return feature


class GeoJsonExporter(JsonItemExporter):

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(('type', 'Feature'))
        feature.append(('properties', item_to_properties(item)))

        if item.get('lon'):
            feature.append(('geometry', {
                'type': 'Point',
                'coordinates': [
                    item['lon'],
                    item['lat']
                ],
            }))

        return feature

    def start_exporting(self):
        self.file.write(to_bytes('{"type":"FeatureCollection","features":[', self.encoding))

    def finish_exporting(self):
        self.file.write(to_bytes(']}', self.encoding))
