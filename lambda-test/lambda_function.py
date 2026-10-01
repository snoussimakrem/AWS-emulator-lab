def handler(event, context):
    return {
        "statusCode": 200,
        "body": f"Hello from Lambda! Received: {event}"
    }
