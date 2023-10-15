# Gaspy App/API Flow

All requests are relative to `https://gaspy.nz/api/v1`

## 1. Login Process

Open the app

### 1.1 Init

The client makes a request to `/Public/init?gold_key&v=10`

The response has some set-cookie headers for session and CSRF tokens. Namely, `SESSION` and `XSRF-TOKEN`.

Response body:

```json
{
	"success": true,
	"data": {
		"review_distance": 0.05,
		"takeover_screen": "1",
		"ev_price_lifespan": 181,
		"fuel_price_lifespan": 8,
		"garage_vehicles_limit": 10,
		"takeover_screens": null,
		"hidden_features": ["missions_and_inventory", "newsletter_integration_outbound_calls"],
		"bottom_wording": "Please update to the latest version of Gaspy"
	}
}
```

### 1.2 Check User

Note: This could be skipped.

The app asks for just the user's email, it then checks to see if that user exists, to then view a login prompt or sign up prompt.

POST Request to `/Public/checkUser` with the request body of the following format:

```json
{
	"email": "email@example.com",
	"v": 10
}
```

Example Resonse:

```json
{
	"success": true,
	"data": {
		"found": true
	}
}
```

### 1.3 Login

POST request to `/Public/login` with a request body of the following format:

```json
{
	"email": "email@example.com",
	"password": "<your_password>",
	"gold_key": null,
	"v": "10"
}
```

Example Response:

```json
{
	"success": true,
	"data": {
		"display_name": "<my_display_name>"
		...
	}
}
```

This repsonse has a whole lot of information in it, like a list of fuel types and brands.

## 2 Fuel Prices

### 2.1 Searching

POST request to `/FuelPrice/searchFuelPricesV2` with a request body of the following format:

```json
{
	"longitude": 176.838112,
	"latitude": -39.54649,
	"distance": 20,
	"order_by": "price",
	"fuel_type_id": 1,
	"ev_plug_types": [5],
	"device_type": "A",
	"v": "10"
}
```

I currently do not know what format the response body is in and how to decode it. It looks to be 2 base64 blobs of data. Where the second blob is much larger than the first. The two blobs are seperated by a colon:

`<first_base64_blob>:<second_base64_blob>`
