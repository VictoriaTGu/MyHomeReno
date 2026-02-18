"""Mock SerpAPI responses for testing Home Depot search."""

# Example response from SerpAPI for Home Depot search: "cordless drill kit"
MOCK_HOMEDEPOT_RESPONSE = {
    "search_metadata": {
        "id": "example_id",
        "status": "Success",
        "json_endpoint": "https://serpapi.com/api/search",
        "created_at": "2024-01-01T00:00:00Z",
        "processed_at": "2024-01-01T00:00:01Z",
        "google_url": "https://www.homedepot.com/s/cordless drill kit"
    },
    "products": [
        {
            "position": 1,
            "title": "DEWALT 20-Volt Compact Cordless Drill/Driver Kit with 1.3 Ah Battery & Charger",
            "product_id": "205521897",
            "price": 98.97,
            "currency": "USD",
            "link": "https://www.homedepot.com/p/DEWALT-20-Volt-Compact-Cordless-Drill-Driver-Kit-with-1-3-Ah-Battery-Charger-DCK201C2/205521897",
            "thumbnails": [
                [
                    "https://images.homedepot-static.com/productImages/abcd1234/abcd1234_s.jpg",
                    "https://images.homedepot-static.com/productImages/abcd1234/abcd1234_m.jpg",
                    "https://images.homedepot-static.com/productImages/abcd1234/abcd1234_l.jpg"
                ]
            ]
        },
        {
            "position": 2,
            "title": "Makita 18V Cordless Compact Drill Kit, 1.5 Ah, with Hard Case",
            "product_id": "205512345",
            "price": 89.99,
            "currency": "USD",
            "link": "https://www.homedepot.com/p/Makita-18V-Cordless-Compact-Drill-Kit/205512345",
            "thumbnails": [
                [
                    "https://images.homedepot-static.com/productImages/efgh5678/efgh5678_s.jpg"
                ]
            ]
        },
        {
            "position": 3,
            "title": "BLACK+DECKER 12V Cordless Drill-Driver Kit",
            "product_id": "205500001",
            "price": 49.98,
            "currency": "USD",
            "link": "https://www.homedepot.com/p/BLACK-DECKER-12V-Cordless-Drill-Driver-Kit/205500001",
            "thumbnails": [
                [
                    "https://images.homedepot-static.com/productImages/ijkl9012/ijkl9012_s.jpg"
                ]
            ]
        }
    ]
}

# Response with missing fields to test error handling
MOCK_HOMEDEPOT_RESPONSE_INCOMPLETE = {
    "search_metadata": {
        "status": "Success"
    },
    "products": [
        {
            "title": "Drill Kit No Price",
            # Missing: product_id, price, link, thumbnails
        },
        {
            "product_id": "123456",
            # Missing: title, price
            "price": 79.99,
        }
    ]
}

# Response indicating an API error
MOCK_HOMEDEPOT_RESPONSE_ERROR = {
    "search_metadata": {
        "status": "Failed",
        "error": "Invalid API key"
    },
    "products": []
}
