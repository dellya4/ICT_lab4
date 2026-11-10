import os
import uuid
import socket
import boto3
import redis

from datetime import datetime
from flask import Flask, request, jsonify
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError


app = Flask(__name__)


BUCKET = os.environ.get("BUCKET", "lab4-files")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT")

s3 = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
    endpoint_url=S3_ENDPOINT,
    config=Config(
        s3={"addressing_style": "path"}
    ) if S3_ENDPOINT else None,
)


def ensure_bucket():
    try:
        s3.head_bucket(Bucket=BUCKET)

    except ClientError:
        s3.create_bucket(Bucket=BUCKET)


REDIS_HOST = os.environ.get(
    "REDIS_HOST",
    "127.0.0.1"
)

REDIS_PRIMARY_PORT = int(
    os.environ.get(
        "REDIS_PRIMARY_PORT",
        "6379"
    )
)

REDIS_REPLICA_PORT = int(
    os.environ.get(
        "REDIS_REPLICA_PORT",
        "6380"
    )
)


primary = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PRIMARY_PORT,
    decode_responses=True,
    socket_timeout=2
)


replica = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_REPLICA_PORT,
    decode_responses=True,
    socket_timeout=2
)


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({
            "error": "field 'message' is required"
        }), 400

    if not isinstance(data["message"], str):
        return jsonify({
            "error": "field 'message' must be a string"
        }), 400

    return jsonify({
        "reply": data["message"]
    }), 200


@app.route("/time", methods=["GET"])
def get_time():
    return jsonify({
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "served_by": socket.gethostname()
    }), 200


@app.route("/files", methods=["POST"])
def save_file():
    data = request.get_json(silent=True)

    if not data or "text" not in data:
        return jsonify({
            "error": "field 'text' is required"
        }), 400

    text = data["text"]

    if not isinstance(text, str):
        return jsonify({
            "error": "field 'text' must be a string"
        }), 400

    encoded = text.encode("utf-8")

    # 10 KB limit
    if len(encoded) > 10_000:
        return jsonify({
            "error": "file is too large"
        }), 400

    file_id = str(uuid.uuid4())

    key = f"files/{file_id}.txt"

    try:
        ensure_bucket()

        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=encoded
        )

    except (ClientError, BotoCoreError):
        return jsonify({
            "error": "storage unavailable"
        }), 503

    return jsonify({
        "file_id": file_id
    }), 201


@app.route("/files/<file_id>", methods=["GET"])
def read_file(file_id):
    try:
        uuid.UUID(file_id)

    except ValueError:
        return jsonify({
            "error": "file not found"
        }), 404

    key = f"files/{file_id}.txt"

    try:
        obj = s3.get_object(
            Bucket=BUCKET,
            Key=key
        )

        text = obj["Body"].read().decode(
            "utf-8"
        )

    except ClientError as error:
        code = error.response["Error"]["Code"]

        if code in (
            "NoSuchKey",
            "NoSuchBucket",
            "404"
        ):
            return jsonify({
                "error": "file not found"
            }), 404

        return jsonify({
            "error": "storage unavailable"
        }), 503

    except BotoCoreError:
        return jsonify({
            "error": "storage unavailable"
        }), 503

    return jsonify({
        "file_id": file_id,
        "text": text
    }), 200


@app.route(
    "/counter/increment",
    methods=["POST"]
)
def increment_counter():
    try:
        value = primary.incr("counter")

    except redis.exceptions.RedisError:
        return jsonify({
            "error": "storage unavailable"
        }), 503

    return jsonify({
        "value": value,
        "source": "primary"
    }), 200


@app.route("/counter", methods=["GET"])
def get_counter():
    source = request.args.get(
        "from",
        "primary"
    )

    if source not in (
        "primary",
        "replica"
    ):
        return jsonify({
            "error": "invalid source"
        }), 400

    client = (
        replica
        if source == "replica"
        else primary
    )

    try:
        value = client.get("counter")

    except redis.exceptions.RedisError:
        return jsonify({
            "error": "storage unavailable"
        }), 503

    return jsonify({
        "value": int(value or 0),
        "source": source
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "resource not found"
    }), 404


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )