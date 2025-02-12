from parsel.selector import Selector

from locations.microdata_parser import MicrodataParser


def test_itemref():
    src = """
<main itemscope itemtype="http://schema.org/GroceryStore">
    <article itemref="schema-location" itemprop="event" itemscope itemtype="http://schema.org/Event">
        <div id="schema-location" itemprop="location" itemscope itemtype="http://schema.org/Place"><span itemprop="name">Test</span></div>
    </article>
</main>
    """
    doc = Selector(text=src)
    items = MicrodataParser.extract_microdata(doc)
    assert items == {
        "items": [
            {
                "type": ["http://schema.org/GroceryStore"],
                "properties": {
                    "event": [
                        {
                            "type": ["http://schema.org/Event"],
                            "properties": {
                                "location": [
                                    {
                                        "type": ["http://schema.org/Place"],
                                        "properties": {"name": ["Test"]},
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]
    }
    ld = MicrodataParser.convert_to_graph(items)
    assert ld == {
        "@context": "https://schema.org",
        "@type": "GroceryStore",
        "event": {"@type": "Event", "location": {"@type": "Place", "name": "Test"}},
    }


# Example from https://branches.lloydsbank.com/aldershot/115-victoria-road where there are multiple address objects,
# but one is empty
def test_multiple_addresses():
    src = """
<main itemscope itemtype="http://schema.org/BankOrCreditUnion" itemid="https://branches.lloydsbank.com/#15682237">
    <span itemprop="name"><span class="LocationName-brand">Lloyds Bank</span> <span class="LocationName-geo">Aldershot</span></span>
    <a href="" itemscope itemtype="http://schema.org/PostalAddress" itemprop="address">
        <div class="Core-mobileAddressContainer">
            <span class="Core-addressRow">115 Victoria Road</span>
            <span class="Core-addressRow">Aldershot, GU11 1JQ</span>
        </div>
    </a>
    <address itemscope itemtype="http://schema.org/PostalAddress" itemprop="address" data-country="GB">
        <meta itemprop="addressLocality" content="Aldershot">
        <meta itemprop="streetAddress" content="115 Victoria Road">
        <div class="c-AddressRow">
            <span class="c-address-street-1">115 Victoria Road</span>
        </div>
        <div class="c-AddressRow">
            <span class="c-address-city">Aldershot</span>
            <span class="c-address-postal-code" itemprop="postalCode">GU11 1JQ</span>
        </div>
        <div class="c-AddressRow">
            <abbr title="United Kingdom" aria-label="United Kingdom" class="c-address-country-name c-address-country-gb" itemprop="addressCountry">GB</abbr>
        </div>
    </address>
</main>
    """
    doc = Selector(text=src)
    items = MicrodataParser.extract_microdata(doc)
    assert items == {
        "items": [
            {
                "id": "https://branches.lloydsbank.com/#15682237",
                "type": ["http://schema.org/BankOrCreditUnion"],
                "properties": {
                    "name": ["Lloyds Bank Aldershot"],
                    "address": [
                        {
                            "type": ["http://schema.org/PostalAddress"],
                            "properties": {},
                        },
                        {
                            "type": ["http://schema.org/PostalAddress"],
                            "properties": {
                                "addressLocality": ["Aldershot"],
                                "streetAddress": ["115 Victoria Road"],
                                "postalCode": ["GU11 1JQ"],
                                "addressCountry": ["GB"],
                            },
                        },
                    ],
                },
            }
        ]
    }
    ld = MicrodataParser.convert_to_graph(items)
    assert ld == {
        "@context": "https://schema.org",
        "@id": "https://branches.lloydsbank.com/#15682237",
        "@type": "BankOrCreditUnion",
        "name": "Lloyds Bank Aldershot",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Aldershot",
            "streetAddress": "115 Victoria Road",
            "postalCode": "GU11 1JQ",
            "addressCountry": "GB",
        },
    }


def test_rdfa():
    src = """
<main vocab="http://schema.org/" typeof="GroceryStore">
    <article property="event" typeof="Event">
        <div id="schema-location" property="location" typeof="Place">
            <span property="name">Test</span>
            <meta property="branchCode" content="001">
        </div>
    </article>
</main>
    """
    doc = Selector(text=src)
    items = MicrodataParser.extract_microdata(doc)
    assert items == {
        "items": [
            {
                "type": ["http://schema.org/GroceryStore"],
                "properties": {
                    "event": [
                        {
                            "type": ["http://schema.org/Event"],
                            "properties": {
                                "location": [
                                    {
                                        "type": ["http://schema.org/Place"],
                                        "properties": {
                                            "name": ["Test"],
                                            "branchCode": ["001"],
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]
    }
    ld = MicrodataParser.convert_to_graph(items)
    assert ld == {
        "@context": "https://schema.org",
        "@type": "GroceryStore",
        "event": {"@type": "Event", "location": {"@type": "Place", "name": "Test", "branchCode": "001"}},
    }
