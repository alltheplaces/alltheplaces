from typing import Iterable

from pyproj import Transformer
from scrapy.http import Request, Response
from scrapy.selector import Selector
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class MerriBekCityCouncilParksAUSpider(XMLFeedSpider):
    name = "merri_bek_city_council_parks_au"
    item_attributes = {"operator": "Merri-bek City Council", "operator_wikidata": "Q30267291", "state": "VIC"}
    allowed_domains = ["www.merri-bek.vic.gov.au"]
    start_urls = [
        "https://www.merri-bek.vic.gov.au/Proxy/proxy.ashx?https%3A%2F%2Fgeo.moreland.vic.gov.au%2Fgeoserver%2FMoreland%2Fows"
    ]
    iterator = "xml"
    namespaces = [
        ("gml", "http://www.opengis.net/gml"),
        ("Moreland", "http://www.moreland.vic.gov.au"),
    ]
    itertag = "gml:featureMember"

    def start_requests(self) -> Iterable[Request]:
        request_body = """<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-transaction.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<wfs:Query typeName="feature:OpenSpace" xmlns:feature="http://www.moreland.vic.gov.au">
		<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
			<ogc:And>
				<ogc:PropertyIsEqualTo>
					<ogc:PropertyName>Website</ogc:PropertyName>
					<ogc:Literal>Yes</ogc:Literal>
				</ogc:PropertyIsEqualTo>
			</ogc:And>
		</ogc:Filter>
	</wfs:Query>
</wfs:GetFeature>"""  # noqa:W191,E101
        headers = {"Content-Type": "application/xml"}
        yield Request(url=self.start_urls[0], body=request_body, headers=headers, method="POST")

    def parse_node(self, response: Response, selector: Selector) -> Iterable[Feature]:
        properties = {
            "ref": selector.xpath("./Moreland:OpenSpace/Moreland:GIS_UID/text()").get(),
            "name": selector.xpath("./Moreland:OpenSpace/Moreland:Name/text()").get(),
            "addr_full": selector.xpath("./Moreland:OpenSpace/Moreland:Full_Addre/text()").get(),
            "city": selector.xpath("./Moreland:OpenSpace/Moreland:Suburb/text()").get(),
            "website": selector.xpath("./Moreland:OpenSpace/Moreland:MCC_webLin/text()").get(),
        }
        source_projection = int(
            selector.xpath("./Moreland:OpenSpace/Moreland:the_geom/gml:Point/@srsName").get().split("#", 1)[1]
        )
        lon_source, lat_source = (
            selector.xpath("./Moreland:OpenSpace/Moreland:the_geom/gml:Point/gml:coordinates/text()")
            .get()
            .split(",", 1)
        )
        properties["lat"], properties["lon"] = Transformer.from_crs(source_projection, 4326).transform(
            lon_source, lat_source
        )
        apply_category(Categories.LEISURE_PARK, properties)
        properties["extras"]["access"] = "yes"
        yield Feature(**properties)
