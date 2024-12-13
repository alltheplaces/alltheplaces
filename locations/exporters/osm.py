import logging
from xml.sax.saxutils import XMLGenerator

from scrapy.exporters import XmlItemExporter

from locations.exporters.geojson import item_to_properties, mapping
from locations.items import get_lat_lon


# NOTE: do not use, this only exports nodes.
class OSMExporter(XmlItemExporter):
    next_id = -1
    item_element = "node"
    root_element = "osm"
    indent = 2
    export_empty_fields = False
    fields_to_export = dict(mapping)
    encoding = "UTF-8"

    def __init__(self, file, **kwargs):
        logging.warning("Deprecated, no not use!")
        self.xg = XMLGenerator(file, encoding=self.encoding, short_empty_elements=True)

    def start_exporting(self):
        self.xg.startDocument()
        self.xg.startElement("osm", {"version": "0.6", "upload": "never", "generator": "All The Places"})
        self._beautify_newline(new_item=True)

    def export_item(self, item):
        coords = get_lat_lon(item)
        if not coords:
            coords = (0, 0)
        self._beautify_indent(depth=1)
        self.xg.startElement(self.item_element, {"id": str(self.next_id), "lat": str(coords[0]), "lon": str(coords[1])})
        self.next_id -= 1
        self._beautify_newline()
        for name, value in self._get_serialized_fields(item, default_value=""):
            self._export_xml_field(name, value, depth=2)
        self._beautify_indent(depth=1)
        self.xg.endElement(self.item_element)
        self._beautify_newline(new_item=True)

    def serialize_field(self, field, name, value):
        assert isinstance(value, str)
        return value

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        yield from item_to_properties(item).items()

    def _export_xml_field(self, name, serialized_value, depth):
        self._beautify_indent(depth=depth)
        if not isinstance(serialized_value, str):
            raise Exception("{} is {} not str".format(name, type(serialized_value).__name__))
        self.xg.startElement("tag", {"k": name, "v": serialized_value})
        self.xg.endElement("tag")
        self._beautify_newline()
