import json
import re
from typing import Union
from urllib.parse import urljoin

import lxml
import parsel
import scrapy


def token_split(val):
    return re.findall(r"\S+", val, flags=re.ASCII)


def top_level_items(selector: parsel.Selector):
    yield from selector.xpath("//*[(@itemscope and not(@itemprop)) or (@typeof and not(@property))]")


def property_value(element: lxml.html.HtmlElement):
    # 5.2.4 Values

    # The property value of a name-value pair added by an element with an
    # itemprop attribute is as given for the first matching case in the
    # following list:

    # If the element also has an itemscope attribute
    if "itemscope" in element.attrib or "typeof" in element.attrib:
        # The value is the item created by the element.
        return element
    # If the element is a meta element
    elif element.tag == "meta":
        # The value is the value of the element's content attribute, if any, or
        # the empty string if there is no such attribute.
        value = element.attrib.get("content", "")
        return value
    # If the element is an audio, embed, iframe, img, source, track, or video
    # element
    elif element.tag in ["audio", "embed", "iframe", "img", "source", "track", "video"]:
        # The value is the resulting URL string that results from parsing the
        # value of the element's src attribute relative to the node document of
        # the element at the time the attribute is set, or the empty string if
        # there is no such attribute or if parsing it results in an error.
        value = element.attrib.get("src", "")
        try:
            value = urljoin(element.base_url, value)
        except ValueError:
            value = None
        return value
    # If the element is an a, area, or link element
    elif element.tag in ["a", "area", "link"]:
        # The value is the resulting URL string that results from parsing the
        # value of the element's href attribute relative to the node document
        # of the element at the time the attribute is set, or the empty string
        # if there is no such attribute or if parsing it results in an error.
        value = element.attrib.get("href", "")
        try:
            value = urljoin(element.base_url, value)
        except ValueError:
            value = None
        return value
    # If the element is an object element
    elif element.tag == "object":
        # The value is the resulting URL string that results from parsing the
        # value of the element's data attribute relative to the node document
        # of the element at the time the attribute is set, or the empty string
        # if there is no such attribute or if parsing it results in an error.
        value = element.attrib.get("data", "")
        try:
            value = urljoin(element.base_url, value)
        except ValueError:
            value = None
        return value
    # If the element is a data element
    # If the element is a meter element
    elif element.tag in ["data", "meter"]:
        # The value is the value of the element's value attribute, if it has one,
        # or the empty string otherwise.
        value = element.attrib.get("value", "")
        return value
    # If the element is a time element
    elif element.tag == "time":
        # The value is the element's datetime value.
        # The datetime value of a time element is the value of the element's
        # datetime content attribute, if it has one, otherwise the child text
        # content of the time element.
        if "datetime" in element.attrib:
            value = element.attrib["datetime"]
        else:
            value = element.text_content()
        return value
    # https://github.com/w3c/microdata-rdf/issues/26
    # https://github.com/w3c/microdata/issues/20
    # Allow @content on any element
    elif "content" in element.attrib:
        value = element.attrib["content"]
        return value
    # Otherwise
    else:
        # The value is the element's descendant text content.
        value = " ".join(filter(None, list(map(str.strip, list(element.itertext())))))
        return value


def item_props(scope: lxml.html.HtmlElement):
    assert "itemscope" in scope.attrib or "typeof" in scope.attrib
    # 5.2.5 Associating names with items

    # 1. Let results, memory, and pending be empty lists of elements.
    results = []
    memory = []
    pending = []

    # 2. Add the element root to memory.
    memory.append(scope)

    # 3. Add the child elements of root, if any, to pending.
    pending.extend(scope.getchildren())

    # 4. If root has an itemref attribute, split the value of that itemref
    # attribute on ASCII whitespace. For each resulting token ID, if there is
    # an element in the tree of root with the ID ID, then add the first such
    # element to pending.
    id_tokens = token_split(scope.attrib.get("itemref", ""))
    docroot = scope.getroottree().getroot()
    for token in id_tokens:
        try:
            ele = docroot.get_element_by_id(token)
            pending.append(ele)
        except KeyError:
            pass
    # 5. While pending is not empty:
    while pending:
        # 5. 1. Remove an element from pending and let current be that element.
        current = pending.pop(0)
        # 5. 2. If current is already in memory, there is a microdata error;
        # continue.
        if current in memory:
            # FIXME show a warning?
            continue

        # 5. 3. Add current to memory.
        memory.append(current)

        # 5. 4. If current does not have an itemscope attribute, then: add all
        # the child elements of current to pending.
        if "itemscope" not in current.attrib and "typeof" not in current.attrib:
            pending.extend(current.getchildren())

        # 5. 5. If current has an itemprop attribute specified and has one or
        # more property names, then add current to results.
        prop_tokens = token_split(current.attrib.get("itemprop", current.attrib.get("property", "")))
        if prop_tokens:
            results.append(current)

    # 6. Sort results in tree order.

    # 7. Return results.
    return results


def get_object(item: lxml.html.HtmlElement, memory=None):
    # 1. Let result be an empty object.
    result = {}
    # 2. If no memory was passed to the algorithm, let memory be an empty list.
    if memory is None:
        memory = []
    # 3. Add item to memory.
    memory.append(item)

    # 4. If the item has any item types, add an entry to result called "type"
    # whose value is an array listing the item types of item, in the order they
    # were specified on the itemtype attribute.
    if item_type := token_split(item.attrib.get("itemtype", "")):
        result["type"] = item_type
    elif item_type := token_split(item.attrib.get("typeof", "")):
        schema = item.attrib.get("vocab", "http://schema.org/")
        result["type"] = [schema + it for it in item_type]

    # 5. If the item has a global identifier, add an entry to result called
    # "id" whose value is the global identifier of item.
    if itemid := item.attrib.get("itemid"):
        try:
            value = urljoin(item.base_url, itemid)
            result["id"] = value
        except ValueError:
            pass

    # 6. Let properties be an empty object.
    properties = {}

    # 7. For each element element that has one or more property names and is
    # one of the properties of the item item, in the order those elements are
    # given by the algorithm that returns the properties of an item, run the
    # following substeps:
    for element in item_props(item):
        # 7.1. Let value be the property value of element.
        value = property_value(element)

        # 7.2. If value is an item, then: If value is in memory, then let value
        # be the string "ERROR". Otherwise, get the object for value, passing a
        # copy of memory, and then replace value with the object returned from
        # those steps.
        if isinstance(value, lxml.html.HtmlElement):
            if value in memory:
                value = "ERROR"
            else:
                value = get_object(value, memory[:])

        # 7.3. For each name name in element's property names, run the
        # following substeps:
        for name in token_split(element.attrib.get("itemprop", element.attrib.get("property", ""))):
            # 7.3.1. If there is no entry named name in properties, then add an
            # entry named name to properties whose value is an empty array.
            if name not in properties:
                properties[name] = []

            # 7.3.2. Append value to the entry named name in properties.
            properties[name] += [value]

    # 8. Add an entry to result called "properties" whose value is the object
    # properties.
    result["properties"] = properties

    # 9. Return result.
    return result


# Python cowardly refuses to hash a dict
# Otherwise, this would be: list(dict.fromkeys(lst))
# Treat unhashable objects as distinct
def hash_obj(val):
    try:
        return hash(val)
    except TypeError:
        return id(val)


def remove_duplicates(lst):
    # Return a new list without duplicates
    seen = set()
    result = []
    for v in lst:
        if (h := hash_obj(v)) not in seen:
            result.append(v)
            seen.add(h)
    return result


def remove_prefix(input_string, prefix):
    if prefix and input_string.startswith(prefix):
        return input_string[len(prefix) :]
    return input_string


def convert_item(item):
    ld = {}
    for itemtype in item.get("type", []):
        schema_type = itemtype
        for schema in ["http://", "https://"]:
            for host in ["schema.org", "www.schema.org"]:
                prefix = f"{schema}{host}/"
                schema_type = remove_prefix(schema_type, prefix)
        if schema_type != itemtype:
            # Did we identify the URI prefix?
            ld["@type"] = schema_type
    if "@type" not in ld:
        return
    # Convert literal values as-is; convert objects recursively
    # Properties is a list; if its length is 1 then flatten, else don't.
    if itemid := item.get("id"):
        ld["@id"] = itemid
    if len(item["properties"].items()) == 0:
        # Guard against goofy use of microdata such as:
        # <a itemscope itemprop=address itemtype=PostalAddress>...</a>
        # Which produce an item with no properties and make it difficult to
        # parse the correct item later down. See test_multiple_addresses
        return
    for k, v in item["properties"].items():
        ld[k] = filter(None, [convert_item(val) if isinstance(val, dict) else val for val in v])
        ld[k] = remove_duplicates(ld[k])
        if len(ld[k]) == 1:
            ld[k] = ld[k][0]
    return ld


def gen_json_ld(result):
    for item in result["items"]:
        obj = convert_item(item)
        if obj is not None:
            yield obj


class MicrodataParser:
    @staticmethod
    def convert_to_graph(result):
        graph = list(gen_json_ld(result))
        if len(graph) == 1:
            result = {"@context": "https://schema.org", **graph[0]}
        else:
            result = {"@context": "https://schema.org", "@graph": graph}
        return result

    @staticmethod
    def extract_microdata(doc: parsel.Selector):
        # 1. Let result be an empty object.
        result = {}
        # 2. Let items be an empty array.
        items = []
        # 3. For each node in nodes, check if the element is a top-level microdata
        # item, and if it is then get the object for that element and add it to
        # items.
        for item in top_level_items(doc):
            items.append(get_object(item.root))

        # 4. Add an entry to result called "items" whose value is the array items.
        result["items"] = items

        # 5. Return the result of serializing result to JSON in the shortest
        # possible way (meaning no whitespace between tokens, no unnecessary zero
        # digits in numbers, and only using Unicode escapes in strings for
        # characters that do not have a dedicated escape sequence), and with a
        # lowercase "e" used, when appropriate, in the representation of any
        # numbers. [JSON]
        return result

    @staticmethod
    def convert_to_json_ld(response: Union["parsel.Selector", "scrapy.http.Response"]):
        selector = getattr(response, "selector", response)
        obj = MicrodataParser.extract_microdata(selector)
        ld = MicrodataParser.convert_to_graph(obj)
        script = selector.root.makeelement("script", {"type": "application/ld+json"})
        script.text = json.dumps(ld, indent=2)
        selector.root.append(script)
