import os
import json
import base64
from datetime import datetime

import requests
from firebase_functions import https_fn


def get_base_url() -> str:
    env = os.environ.get("MPESA_ENV", "sandbox").lower()
    if env == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def get_access_token() -> str:
    consumer_key = os.environ["MPESA_CONSUMER_KEY"]
    consumer_secret = os.environ["MPESA_CONSUMER_SECRET"]
    url = f"{get_base_url()}/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(consumer_key, consumer_secret),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Access token missing: {data}")

    return token


def generate_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def normalize_phone_number(phone: str) -> str:
    phone = phone.strip().replace("+", "")

    if phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    if phone.startswith("7") and len(phone) == 9:
        return "254" + phone
    if phone.startswith("254") and len(phone) == 12:
        return phone

    raise ValueError("Phone must be 0712345678, 712345678, or 254712345678")


def get_cors_headers(req: https_fn.Request) -> dict:
    """
    Return CORS headers, allowing requests from known Firebase hosting origins
    and localhost for local development.
    """
    ALLOWED_ORIGINS = {
        "https://pdfwebsitedwnld.web.app",
        "https://pdfwebsitedwnld.firebaseapp.com",
        "http://localhost:5000",
        "http://localhost:5001",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5001",
    }
    origin = req.headers.get("Origin", "")
    allowed_origin = origin if origin in ALLOWED_ORIGINS else "https://pdfwebsitedwnld.web.app"

    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


@https_fn.on_request()
def start_stk_push(req: https_fn.Request) -> https_fn.Response:
    headers = get_cors_headers(req)

    if req.method == "OPTIONS":
        return https_fn.Response("", status=204, headers=headers)

    if req.method != "POST":
        return https_fn.Response(
            json.dumps({"error": "Method not allowed"}),
            status=405,
            headers={**headers, "Content-Type": "application/json"},
        )

    try:
        body = req.get_json(silent=True) or {}
        phone = normalize_phone_number(str(body.get("phoneNumber", "")).strip())
        amount = int(body.get("amount", 1))

        if amount < 1:
            raise ValueError("Amount must be at least 1")

        shortcode = os.environ["MPESA_SHORTCODE"]
        passkey = os.environ["MPESA_PASSKEY"]
        callback_url = os.environ["MPESA_CALLBACK_URL"]
        party_b = os.environ.get("MPESA_PARTYB", shortcode)
        transaction_type = os.environ.get("MPESA_TRANSACTION_TYPE", "CustomerPayBillOnline")
        account_reference = os.environ.get("MPESA_ACCOUNT_REFERENCE", "Payment")
        transaction_desc = os.environ.get("MPESA_TRANSACTION_DESC", "Website payment")

        access_token = get_access_token()
        timestamp = generate_timestamp()
        password = generate_password(shortcode, passkey, timestamp)

        stk_url = f"{get_base_url()}/mpesa/stkpush/v1/processrequest"

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": amount,
            "PartyA": phone,
            "PartyB": party_b,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
        }

        response = requests.post(
            stk_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        return https_fn.Response(
            json.dumps(result),
            status=200,
            headers={**headers, "Content-Type": "application/json"},
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=400,
            headers={**headers, "Content-Type": "application/json"},
        )


@https_fn.on_request()
def mpesa_callback(req: https_fn.Request) -> https_fn.Response:
    try:
        body = req.get_json(silent=True) or {}
        print("M-Pesa callback:", json.dumps(body))
        return https_fn.Response(
            json.dumps({"ResultCode": 0, "ResultDesc": "Accepted"}),
            status=200,
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=400,
            headers={"Content-Type": "application/json"},
        )