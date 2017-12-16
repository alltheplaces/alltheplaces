import scrapy
import xml.etree.ElementTree as ET

from locations.items import GeojsonPointItem


URL = 'http://hosted.where2getit.com/auntieannes/2014/ajax?&xml_request=%3Crequest%3E%3Cappkey%3E6B95F8A2-0C8A-11DF-A056-A52C2C77206B%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Climit%3E2500%3C%2Flimit%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3EMinneapolis+MN+55412%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Csearchradius%3E5000%3C%2Fsearchradius%3E%3C%2Fformdata%3E%3C%2Frequest%3E'


TAGS = [
        'city', 'country', 'latitude', 'longitude',
        'phone', 'postalcode', 'state', 'uid'
]

MAPPING = {
    'latitude': 'lat', 'longitude': 'lon', 'uid': 'ref',
    'postalcode': 'postcode',
}


class ClassName(scrapy.Spider):

    name = "aunt_annes"
    start_urls = (
            URL,
        )
    allowed_domains = ["hosted.where2getit.com/auntieannes"]
    download_delay = 0.2

    def process_poi(self, poi):
        props = {}
        add_parts = []

        for child in poi:
            if child.tag in TAGS and child.tag in MAPPING:
                if child.tag in ('latitude', 'longitude'):
                    props[MAPPING[child.tag]] = float(child.text)
                else:
                    props[MAPPING[child.tag]] = child.text

            elif child.tag in TAGS and child.tag not in MAPPING:
                props[child.tag] = child.text

            elif child.tag in ('address1', 'address2', 'address3', ):
                add_parts.append(child.text if child.text else '')

        props.update({'addr_full': ', '.join(filter(None, add_parts))})
        return GeojsonPointItem(**props)

    def parse(self, response):

        root = ET.fromstring(response.text)
        collection = root.getchildren()[0]
        pois = collection.findall('poi')
        for poi in pois:
            yield self.process_poi(poi)
