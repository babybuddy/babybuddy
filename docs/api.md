# API

Baby Buddy uses the [Django REST Framework](https://www.django-rest-framework.org/)
(DRF) to provide a REST API.

The only requirement for (most) requests is to set the `Authorization` header as
described in the [Authentication](#authentication) section. The one exception is
the `/api` endpoint, which lists all available endpoints and does not require
authorization.

Currently, the following endpoints are available for `GET`, `OPTIONS`, and
`POST` requests:

- `/api/bmi/` (Body Mass Index)
- `/api/children/`
- `/api/changes/` (Diaper Changes)
- `/api/feedings/`
- `/api/head-circumference/`
- `/api/height/`
- `/api/notes/`
- `/api/pumping/`
- `/api/sleep/`
- `/api/tags/`
- `/api/temperature/`
- `/api/timers/`
- `/api/tummy-times/`
- `/api/weight/`

## Authentication

The [TokenAuthentication](https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication)
and [SessionAuthentication](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication)
are enabled by default. Session authentication covers local API requests made by
the application itself. Token authentication allows external requests to be
made.

:exclamation: **In a production environment, token authentication should only
be used for API calls to an `https` endpoint.** :exclamation:

Each user has an API key that can be used for token authentication. This key can
be found on the User Settings page for the logged in the user. To use a key for
an API request, set the request `Authorization` header to `Token <user-key>`. E.g.

    Authorization: Token 2h23807gd72h7hop382p98hd823dw3g665g56

If no `Authorization` header set, or the key is not valid the API will return
`403 Forbidden` with additional details in the response body.

## Schema

The API schema in [OpenAPI format](https://swagger.io/specification/) can be
found in the [`openapi-schema.yml`](https://github.com/babybuddy/babybuddy/tree/master/openapi-schema.yml)
file in the project root. A live version is also available at the `/api/schema` path of
a running instance.

## `GET` Method

### Request

The `limit` and `offset` request parameters can be used to limit
and offset the results set respectively. For example, the following request
will return five diaper changes starting from the 10th diaper change entry:

```shell
curl -X GET 'https://[...]/api/changes/?limit=5&offset=10' -H 'Authorization: Token [...]'
```

```json
{
  "count": 20,
  "next": "https://[...]/api/changes/?limit=5&offset=15",
  "previous": "https://[...]/api/changes/?limit=5&offset=5",
  "results": []
}
```

Field-based filters for specific endpoints can be found the in the `filters`
field of the `OPTIONS` response for specific endpoints.

Single entries can also be retrieved by adding the ID (or in the case of a
Child entry, the slug) of a particular entry:

```shell
curl -X GET https://[...]/api/children/gregory-hill/ -H 'Authorization: Token [...]'
```

```json
{
  "id": 3,
  "first_name": "Gregory",
  "last_name": "Hill",
  "birth_date": "2020-02-11",
  "slug": "gregory-hill",
  "picture": null
}
```

```shell
curl -X GET https://[...]/api/sleep/1/ -H 'Authorization: Token [...]'
```

```json
{
  "id": 480,
  "child": 3,
  "start": "2020-03-12T21:25:28.916016-07:00",
  "end": "2020-03-13T01:34:28.916016-07:00",
  "duration": "04:09:00",
  "nap": false
}
```

### Response

Returns JSON data in the response body in the following format:

```json
{
    "count":<int>,
    "next":<url>,
    "previous":<url>,
    "results":[{...}]
}
```

- `count`: Total number of records (_in the database_, not just the response).
- `next`: URL for the next set of results.
- `previous`: URL for the previous set of results.
- `results`: An array of the results of the request.

For single entries, returns JSON data in the response body keyed by model field
names. This will vary between models.

## `OPTIONS` Method

### Request

All endpoints will respond to an `OPTIONS` request with detailed information
about the endpoint's purpose, parameters, filters, etc.

### Response

Returns JSON data in the response body describing the endpoint, available
options for `POST` requests, and available filters for `GET` requests. The
following example describes the `/api/children` endpoint:

```json
{
    "name": "Child List",
    "renders": [
        "application/json",
        "text/html"
    ],
    "parses": [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ],
    "actions": {
        "POST": {
            "id": {
                "type": "integer",
                "required": false,
                "read_only": true,
                "label": "ID"
            },
            [...]
        }
    },
    "filters": [
        "first_name",
        "last_name",
        "slug"
    ]
}
```

## `POST` Method

### Request

To add new entries for a particular endpoint, send a `POST` request with the
entry data in JSON format in the request body. The `Content-Type` header for
`POST` request must be set to `application/json`.

Regular sanity checks will be performed on relevant data. See the `OPTIONS`
response for a particular endpoint for details on required fields and data
formats.

### Timer Field

`POST` requests also accept a `timer` field to model endpoints supporting duration
(Feeding, Sleep, Tummy Time). Set `timer` to a valid timer ID in a request instead of
the `start` and `end` fields. The new entry will use the `start` and `end` values
_from the Timer_ and if the timer is running it will be stopped by this operation.

Additionally, if the Timer has a child relationship, the `child` field will be
filled in automatically with the `child` value from the Timer.

The `timer` field will **always override** the relevant fields (`child`, `start`,
and `end`) on the request. E.g., a `POST` request with both the `timer` and `end`
fields will ignore the `end` field value and replace it with the Timer's `end`
value. The same applies for `start` and `child`. These fields are all **required**
if the `timer` field is _not_ set.

#### Example `timer` field usage

Create a new timer associated with a `child`:

```shell
curl --location --request POST '[...]/api/timers/' \
--header 'Authorization: Token [...]' \
--header 'Content-Type: application/json' \
--data-raw '{"child": 1}'
```

Note the timer `id` in the response:

```json
{
  "id": 5,
  "child": 1,
  "name": null,
  "start": "2022-05-28T19:59:40.013914Z",
  "duration": null,
  "user": 1
}
```

Create a new tummy time entry supplying only the timer `id`:

```shell
curl --location --request POST '[...]/api/tummy-times/' \
--header 'Authorization: Token [...]' \
--header 'Content-Type: application/json' \
--data-raw '{"timer": 5}'
```

Note that `child` and `start` match the timer values (and `end` is auto-populated):

```json
{
  "id": 162,
  "child": 1,
  "start": "2022-05-28T19:59:40.013914Z",
  "end": "2022-05-28T20:01:13.549099Z",
  "duration": "00:01:33.535185",
  "milestone": "",
  "tags": []
}
```

Also note that the timer has been deleted.

### Response

Returns JSON data in the response body describing the added/updated instance or
error details keyed by either the field in error or the general string `non_field_errors`
(e.g., when validation involves multiple fields).

## `PATCH` Method

### Request

To update existing entries, send a `PATCH` request to the single entry endpoint
for the entry to be updated. The `Content-Type` header for `PATCH` request must
be set to `application/json`. For example, to update a Diaper Change entry with
ID 947 to indicate a "wet" diaper only:

```shell
curl -X PATCH \
    -H 'Authorization: Token [...]' \
    -H "Content-Type: application/json" \
    -d '{"wet":1, "solid":0}' \
    https://[...]/api/changes/947/
```

Regular sanity checks will be performed on relevant data. See the `OPTIONS`
response for a particular endpoint for details on required fields and data
formats.

### Response

Returns JSON data in the response body describing the added/updated instance or
error details keyed by either the field in error or the general string `non_field_errors`
(e.g., when validation involves multiple fields).

## `DELETE` Method

### Request

To delete an existing entry, send a `DELETE` request to the single entry
endpoint to be deleted. For example, to delete a Diaper Change entry with ID
947:

```shell
curl -X DELETE https://[...]/api/changes/947/ -H 'Authorization: Token [...]'
```

### Response

Returns an empty response with HTTP status code `204` on success, or a JSON
encoded error detail if an error occurred (e.g. `{"detail":"Not found."}` if
the requested ID does not exist).
