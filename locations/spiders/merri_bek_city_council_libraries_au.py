from pyproj import Transformer
from typing import Iterable

from scrapy.http import Request, Response
from scrapy.selector import Selector
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class MerriBekCityCouncilLibrariesAUSpider(XMLFeedSpider):
    name = "merri_bek_city_council_libraries_au"
    item_attributes = {"operator": "Merri-bek City Council", "operator_wikidata": "Q30267291", "state": "VIC"}
    allowed_domains = ["www.merri-bek.vic.gov.au"]
    start_urls = ["https://www.merri-bek.vic.gov.au/Proxy/proxy.ashx?https%3A%2F%2Fgeo.moreland.vic.gov.au%2Fgeoserver%2FMoreland%2Fows"]
    iterator = "xml"
    namespaces = [
        ("gml", "http://www.opengis.net/gml"),
        ("Moreland", "http://www.moreland.vic.gov.au"),
    ]
    itertag = "gml:featureMember"

    def start_requests(self) -> Iterable[Request]:
        request_body = """<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-transaction.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<wfs:Query typeName="feature:MCC_Facilities" xmlns:feature="http://www.moreland.vic.gov.au">
		<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
			<ogc:And>
				<ogc:PropertyIsLike wildCard="*" singleChar="." escape="!">
					<ogc:PropertyName>Category</ogc:PropertyName>
					<ogc:Literal>Library</ogc:Literal>
				</ogc:PropertyIsLike>
			</ogc:And>
		</ogc:Filter>
	</wfs:Query>
</wfs:GetFeature>"""
        headers = {
            "Content-Type": "application/xml"
        }
        yield Request(url=self.start_urls[0], body=request_body, headers=headers, method="POST")

    def parse_node(self, response: Response, selector: Selector) -> Iterable[Feature]:
        properties = {
            "ref": selector.xpath("./Moreland:MCC_Facilities/Moreland:Asset_ID/text()").get(),
            "name": selector.xpath("./Moreland:MCC_Facilities/Moreland:Label_Name/text()").get(),
            "street_address": selector.xpath("./Moreland:MCC_Facilities/Moreland:Address/text()").get(),
            "city": selector.xpath("./Moreland:MCC_Facilities/Moreland:Suburb/text()").get(),
            "postcode": selector.xpath("./Moreland:MCC_Facilities/Moreland:Postcode/text()").get(),
            "phone": selector.xpath("./Moreland:MCC_Facilities/Moreland:Phone/text()").get(),
            "email": selector.xpath("./Moreland:MCC_Facilities/Moreland:Email/text()").get(),
        }
        source_projection = int(selector.xpath("./Moreland:MCC_Facilities/Moreland:the_geom/gml:Point/@srsName").get().split("#", 1)[1])
        lon_source, lat_source = selector.xpath("./Moreland:MCC_Facilities/Moreland:the_geom/gml:Point/gml:coordinates/text()").get().split(",", 1)
        properties["lat"], properties["lon"] = Transformer.from_crs(source_projection, 4326).transform(lon_source, lat_source)
        apply_category(Categories.LIBRARY, properties)
        properties["extras"]["access"] = "yes"
        yield Feature(**properties)
