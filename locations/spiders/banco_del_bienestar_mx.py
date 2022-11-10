import re

import scrapy
import xmltodict

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.items import GeojsonPointItem


class BancoDelBienestarMXSpider(scrapy.Spider):
    name = "banco_del_bienestar_mx"
    item_attributes = {
        "brand": "Banco del Bienestar",
        "brand_wikidata": "Q5719137",
        "extras": Categories.BANK.value,
    }

    def start_requests(self):
        yield scrapy.Request(
            url="http://www.bansefi.gob.mx/_vti_bin/Lists.asmx",
            method="POST",
            headers={"Content-Type": "text/xml; charset='UTF-8'"},
            body="""<soap:Envelope
                xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
                xmlns:xsd='http://www.w3.org/2001/XMLSchema'
                xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>
                <soap:Body>
                    <GetListItems
                        xmlns='http://schemas.microsoft.com/sharepoint/soap/'>
                        <listName>Sucursales</listName>
                        <viewName></viewName>
                        <query>
                            <Query>
                                <Where>
                                    <Eq>
                                        <FieldRef Name='Tipo' />
                                        <Value Type='Text'>Sucursal</Value>
                                    </Eq>
                                </Where>
                            </Query>
                        </query>
                        <viewFields>
                            <ViewFields>
                                <FieldRef Name='Title' />
                                <FieldRef Name='Estado' />
                                <FieldRef Name='Municipio' />
                                <FieldRef Name='Localidad' />
                                <FieldRef Name='Direccion' />
                                <FieldRef Name='Lada' />
                                <FieldRef Name='Telefono' />
                                <FieldRef Name='Horario' />
                                <FieldRef Name='Localizacion' />
                            </ViewFields>
                        </viewFields>
                        <rowLimit>0</rowLimit>
                        <queryOptions>
                            <QueryOptions></QueryOptions>
                        </queryOptions>
                    </GetListItems>
                </soap:Body>
            </soap:Envelope>""",
        )

    def parse(self, response):
        data = xmltodict.parse(response.body)
        for bank in DictParser.get_nested_key(data, "z:row"):
            item = GeojsonPointItem()
            item["ref"] = bank["@ows_ID"]
            if m := re.match(
                r"POINT\((-?\d+\.\d+) (-?\d+\.\d+)\)", bank.get("@ows_Localizacion", "")
            ):
                item["lon"], item["lat"] = m.groups()
            item["name"] = bank["@ows_Title"]
            item["addr_full"] = bank.get("@ows_Direccion")
            item["city"] = bank.get("@ows_Municipio") or bank.get("@ows_Localidad")
            item["phone"] = ";".join(
                [n.strip() for n in bank.get("@ows_Telefono", "").split("/")]
            )
            yield item
