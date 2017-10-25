# User API Operations

## JSON REST: Object Definitions

This definition lists named resources that can be manipulated using a small number of HTTP methods. 
The ESPA REST JSON API uses standard HTTP methods, in order to do things like `List`, `Get`, `Create`, and `Update`.

* [Schema Definitions](#schema-definitions): Building an order
* [User Authentication](#user-authentication): Testing credentials/access
* [Order Status](#orders-and-scenes): Submitting/checking/downloading an order
* [General API Interactions](#generalApiInteractions): FAQs

### Schema definitions

HTTP Method	| URI	| Action
---|---|---
[GET](#api)  |  `/api/`  |  Lists all available versions of the api.
[GET](#apiOps)  |  `/api/v0`  |  Lists all available api operations.
[GET](#apiProj)  |  `/api/v0/projections`  |  Lists and describes available projections, and their ordering constraints (min/max values, etc.).
[GET](#apiFormats)  |  `/api/v0/formats`  |  Lists all available output filetype formats
[GET](#apiResamp)  |  `/api/v0/resampling-methods`  |  Lists all available resampling methods
[GET](#apiOrderSchema)  |  `/api/v0/order-schema`  |  Retrieves entire order schema definition
[GET](#apiProdsPost)  |  `/api/v0/available-products`  |  Lists available products (`"toa","sr",...`) for the supplied inputs

**Note**: The `available-products` resource maps the input IDs by sensor, or lists as `"not_implemented"` if the values cannot be ordered or determined.

### User Authentication

HTTP Method	| URI	| Action
---|---|---
[GET](#apiUser)  |  `/api/v0/user`  |  Returns user information for the authenticated user.

<details>
<summary>Pro tip</summary>

Use the `$HOME/.netrc` file, for automatic user authentication.   
This allows `curl -n` to handle login, replacing `curl --user <erosusername>:<erospassword>`! 

</details>

### Orders and Scenes

HTTP Method	| URI	| Action
---|---|---
[GET](#apiOrders)  |  `/api/v0/list-orders`  |  List orders for the authenticated user.
[GET](#apiOrdersEmail)  |  `/api/v0/list-orders/<email>`  |  Lists orders for the supplied email. Necessary to support user collaboration
[GET](#apiOrderDetails), [POST](#apiSubmitOrder), [PUT](#apiUpdateOrder)  |  `/api/v0/order/<ordernum>`  |  Retrieves details for a submitted order, or Create/Update existing order
[GET](#apiStatus)  |  `/api/v0/order-status/<ordernum>`  |  Retrieves a submitted orders status
[GET](#apiItemStats)  |  `/api/v0/item-status/<ordernum>`  |  Retrieve the status and details for all products in an order


---

<a id="api"></a>**GET /api**

Lists all available versions of the api.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api
```
```json
// Response:
{
    "v0": "Version 0 of the ESPA API"
}
```

<a id="apiOps"></a>**GET /api/v0**

Lists all available api operations.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0
```
```json
// Response:
{
    "description": "Version 0 of the ESPA API",
    "operations": {
        "/api": {
            "function": "list versions",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0": {
            "function": "list operations",
            "methods": [
                "HEAD",
                "GET"
            ]
        } // ...
    }
}
```

<a id="apiUser"></a>**GET /api/v0/user**

Returns user information for the authenticated user.

```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/user
```
```json
// Response:
{
  "email": "production@email.com",
  "first_name": "Production",
  "last_name": "Person",
  "roles": [
    "active"
  ],
  "username": "production"
}
```
   
<a id="apiProdsGet"></a>**GET /api/v0/available-products/\<product_id\>**

Lists the available output products for the supplied input.

```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/available-products/LE07_L1TP_027027_20160730_20160831_01_T1
```
```json
// Response:
{
    "etm7": {
        "inputs": [
            "LE07_L1TP_029030_20170221_20170319_01_T1"
        ], 
        "products": [
            "source_metadata",
            "stats" // ...
        ]
    }
}
```

<a id="apiProdsPost"></a>**GET /api/v0/available-products**

Lists available products for the supplied inputs.  Also classifies the inputs by sensor or lists as 'not implemented' if the values cannot be ordered or determined.

```bash
curl  --user <erosusername>:<erospassword> \
        -X GET \
        -d '{"inputs":["LE07_L1TP_029030_20170221_20170319_01_T1",
               "MOD09A1.A2000073.h12v11.005.2008238080250.hdf", "bad_scene_id"]}' \
        https://espa.cr.usgs.gov/api/v0/available-products
```
```json
// Response:
{
    "etm7_collection": {
        "inputs": [
            "LE07_L1TP_029030_20170221_20170319_01_T1"
        ], 
        "products": [
            "source_metadata",
            "stats" // ...
        ]
    }, 
    "mod09a1": {
        "inputs": [
            "MOD09A1.A2000073.h12v11.005.2008238080250.hdf"
        ], 
        "outputs": [
            "l1", 
            "stats"
        ]
    }, 
    "not_implemented": [
        "bad_scene_id"
    ]
}
```

<a id="apiProj"></a>**GET /api/v0/projections**

Lists and describes available projections.  This is a dump of the schema defined that constrains projection info.

```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/projections
```
```json
// Response:
{
    "aea": {
        "title": "Albers Equal Area",
        "pixel_units": ["meters", "dd"],
        "properties": {
            "central_meridian": {
                "title": "Central Meridian",
                "maximum": 180, 
                "minimum": -180, 
                "required": true, 
                "type": "number"
            }, 
            "datum": {
                "title": "Datum",
                "enum":{
                    "nad27": "North American Datum 1927",
                    "nad83": "North American Datum 1983",
                    "wgs84": "World Geodetic System 1984"
                }, 
                "required": true, 
                "type": "string"
            } // ...
        },
        "type": "object"
    }, 
    "lonlat": {
        "title": "Geographic",
        "pixel_units": ["dd"],
        "type": "null"
    } // ...
}        
```

<a id="apiFormats"></a>**GET /api/v0/formats**

Lists all available output formats
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/formats
```
```json
// Response: 
{
  "formats": {
    "envi": "ENVI",
    "gtiff": "GeoTiff", // ...
  }
```

<a id="apiResamp"></a>**GET /api/v0/resampling-methods**

Lists all available resampling methods
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/resampling-methods
```
```json
// Response: 
{
  "resampling_methods": {
    "nn": "Nearest Neighbor", 
    "bil": "Bilinear Interpolation", 
    "cc": "Cubic Convolution"
  }
}
```

<a id="apiOrders"></a>**GET /api/v0/list-orders**

List orders for the authenticated user.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/list-orders
```
```json
// Response: 
[
    "production@email.com-101015143201-00132", 
    "production@email.com-101115143201-00132"
]
```

Also accepts JSON filters: 
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/list-orders -X GET -d '{"status": "complete"}'
```

<a id="apiOrdersEmail"></a>**GET /api/v0/list-orders/\<email\>**

Lists orders for the supplied email.  Necessary to support user collaboration.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/list-orders/production@email.com
```
```json
// Response: 
[
    "production@email.com-101015143201-00132", 
    "production@email.com-101115143201-00132"
]
```

<a id="apiStatus"></a>**GET /api/v0/order-status/\<ordernum\>**

Retrieves a submitted orders status
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/order-status/production@usgs.gov-07282016-135122
```
```json
// Response: 
{
 "orderid": "production@usgs.gov-07282016-135122",
 "status": "complete"
}
```

<a id="apiOrderDetails"></a>**GET /api/v0/order/\<ordernum\>**

Retrieves details for a submitted order. Some information may be omitted from this response depending on access privileges.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/order/production@usgs.gov-03072016-081013
```
```json
{
  "completion_date": "2016-08-01T14:47:08.589621",
  "note": "",
  "order_date": "2016-08-01T14:17:48.589621",
  "order_source": "espa",
  "order_type": "level2_ondemand",
  "orderid": "production@usgs.gov-03072016-081013",
  "priority": "normal",
  "product_options": "",
  "product_opts": {
    "format": "gtiff",
    "tm5_collection": {
      "inputs": [
        "LT05_L1TP_026028_20111022_20160830_01_T1"
      ],
      "products": [
        "sr"
      ]
    }
  },
  "status": "complete"
}
```

<a id="apiItemStats"></a>**GET /api/v0/item-status/\<ordernum\>**

Retrieve the status and details for all products in an order.
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/item-status/production@usgs.gov-03072016-081013
```
```json
// Response: 
{
    "production@usgs.gov-07282016-135122": [
        {
            "cksum_download_url": "http://espa.cr.usgs.gov/.../orders/.../LC080270272016072201T1-SC20160728135757.md5",
            "completion_date": "2016-08-01T14:17:08.589621",
            "name": "LE07_L1TP_010028_20050420_20160925_01_T1", 
            "note": "", 
            "product_dload_url": "http://espa.cr.usgs.gov/.../orders/.../LT050260282011102201T1-SC20160804121126.tar.gz",
            "status": "complete"
        },
        {
            "cksum_download_url": "",
            "completion_date": "",
            "name": "LT05_L1TP_026028_20111022_20160830_01_T1", 
            "note": "", 
            "product_dload_url": "",
            "status": "oncache"
        }
    ]
}
```

Also accepts JSON filters: 
```bash
curl --user <erosusername>:<erospassword> \
    -X GET \
    -d '{"status": "complete"}' \
    https://espa.cr.usgs.gov/api/v0/item-status/production@usgs.gov-03072016-081013
```

<a id="apiProdStats"></a>**GET /api/v0/item-status/\<ordernum\>/\<itemnum\>**

Retrieve status and details for a particular product in an order
```bash
curl --user <erosusername>:<erospassword> \
    https://espa.cr.usgs.gov/api/v0/item-status/production@usgs.gov-03072016-081013/LC08_L1TP_027027_20160722_20170221_01_T1
```
```json
{
    "production@usgs.gov-07282016-135122": [
       {
            "cksum_download_url": "http://espa.cr.usgs.gov/.../orders/.../LC080270272016072201T1-SC20160728135757.md5",
            "completion_date": "2016-08-01T14:17:08.589621",
            "name": "LE07_L1TP_010028_20050420_20160925_01_T1", 
            "note": "", 
            "product_dload_url": "http://espa.cr.usgs.gov/.../orders/.../LT050260282011102201T1-SC20160804121126.tar.gz",
            "status": "complete"
        }
    ]
 }
```

<a id="apiSubmitOrder"></a>**POST /api/v0/order**

Accepts requests for process from an HTTP POST with a JSON body. The body is validated against the schema definitions.
Errors are returned to user, successful validation returns an orderid

```bash
curl --user <erosusername>:<erospassword> -d '{"olitirs8_collection": {
                                                    "inputs": ["LC08_L1TP_027027_20160722_20170221_01_T1"], 
                                                    "products": ["sr"]
                                                 }, 
                                     "format": "gtiff", 
                                     "resize": {
                                                "pixel_size": 60, 
                                                "pixel_size_units": "meters"
                                                }, 
                                     "resampling_method": "nn", 
                                     "plot_statistics": true, 
                                     "projection": {
                                                    "aea": {
                                                            "standard_parallel_1": 29.5,
                                                            "standard_parallel_2": 45.5,
                                                            "central_meridian": -96.0,
                                                            "latitude_of_origin": 23.0,
                                                            "false_easting": 0.0,
                                                            "false_northing": 0.0,
                                                            "datum": "wgs84"
                                                            }
                                                    },
                                     "image_extents": {
                                                        "north": 0.0002695,
                                                        "south": 0,
                                                        "east": 0.0002695,
                                                        "west": 0,
                                                        "units": "dd"
                                                    },
                                     "note": "this is going to be sweet..."
                                     }' https://espa.cr.usgs.gov/api/v0/order
```
```json
// Response: 
{
    "orderid": "espa-production@email.com-05232017-150628-847", 
    "status": "ordered"
}
```
<a id="apiUpdateOrder"></a>**PUT /api/v0/order**

Update an order with a JSON body. 

```bash
curl --user <erosusername>:<erospassword> \
    -X PUT \
    -d '{"orderid": "espa-production@email.com-05232017-150628-847", "status": "cancelled"}' \
    https://espa.cr.usgs.gov/api/v0/order
```
```json
// Response:
{
    "orderid": "espa-production@email.com-05232017-150628-847", 
    "status": "cancelled"
}
```

<a id="apiOrderSchema"></a>**GET /api/v0/order-schema**
 
Retrieves order schema definition
```bash
curl --user <erosusername>:<erospassword> https://espa.cr.usgs.gov/api/v0/order-schema
```
```json
// Response:
{
    "extents": 200000000, 
    "oneormoreobjects": [
        "myd13a2", 
        "myd13a3", 
        "mod09gq" // ...
    ], 
    "properties": {
        "etm7_collection": {
            "properties": {
                "inputs": {
                    "ItemCount": "inputs", 
                    "items": {
                        "pattern": "^le07_{1}\\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\\w{2}$", 
                        "type": "string"
                    }, 
                    "minItems": 1, 
                    "required": true, 
                    "type": "array", 
                    "uniqueItems": true
                }, 
                "products": {
                    "items": {
                        "enum": [
                            "source_metadata", 
                            "l1", 
                            "toa" // ...
                        ], 
                        "type": "string"
                    }, 
                    "minItems": 1, 
                    "required": true, 
                    "restricted": true, 
                    "stats": true, 
                    "type": "array", 
                    "uniqueItems": true
                }
            }, 
            "type": "object"
        }, 
        "format": {
            "enum": {
                "envi": "ENVI",
                "gtiff": "GeoTiff",
                "hdf-eos2": "HDF-EOS2",
                "netcdf": "NetCDF"
            }, 
            "title": "Output Format",
            "required": true, 
            "type": "string"
        } // ...
    }, 
    "set_ItemCount": [
        "inputs", 
        5000
    ], 
    "type": "object"
}
``` 

<a id="generalApiInteractions"></a>
## General API Interactions

### Messages

The HTTP Response Code coming from the server is the primary method of alerting users of the results of their request (success/fail). 
In addition to the HTTP Response Code, the JSON response will also include any `"messages"` which will give clarification of the Response Code, and should always be examined.
 
The JSON response will only contain `"messages"` if there is an associated message field contained. It will only contain one object, either: 
1. **Errors**: An un-recoverable error has occurred
  * `"messages": {"errors": [...]}` 
1. **Warnings**: Nothing wrong has occurred inside the system, but these warnings can later elevate to errors (for example, if a product becomes deprecated). 
  * `"messages": {"warnings": [...]}`
  
### HTTP Status Codes

The status code will match the desired behavior, depending on the HTTP Method used:

* GET: Performs searches for current system states
  * `200 OK`: The search was performed successfully (**Note:** the result returned may be an empty object)
  * `401 Authenication Failed`: Could not authenticate the username/password combination
  * `403 Forbidden`: The user is not allowed to access the system
  * `404 Not Found`: The server could not perform the requested operation
* POST: For every request, a new state on the server is created 
  * `201 Created`: A new resource has been created, information of which is included in the response
  * `400 Bad Request`: Unable to parse the supplied message
  * `405 Method Not Allowed`: Cannot perform POST
* PUT: Updates a resource, changing it to the desired state
  * `202 Accepted`: The resource has been updated, and the response represents the new state

There are circumstances when the server supersedes the API, and gives information related to its current configuration: 

* Server maintenance: The server is either down for maintenance, or experiencing extreme difficulties
  * `500 Internal Server Error`: This likely means the server is on fire, and system admins are working to restore it
  * `503 Service Unavailable`: This means the server is down for regular maintenance
* Host redirection: The hostname supplied is now living at a new location
  * `301 Moved Permanently`: Use the location header to navigate to the correct page
    * This is usually used for HTTPS redirection, but will also occur during system maintenance

### Known Issues

* POST requests from most MS Windows terminals/command-prompts require json 
objects be wrapped in double quotes with internal strings wrapped in escaped 
double quotes. For example:
```"{\"olitirs8\": {\"inputs\": [\"LC08_L1TP_027027_20160722_20170221_01_T1\"],\"products...```
For more info, see [Issue #42](https://github.com/USGS-EROS/espa-api/issues/42#issuecomment-263454906)
 