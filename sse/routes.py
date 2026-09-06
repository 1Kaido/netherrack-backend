from flask import Blueprint, Response
from .redis_client import redis_client
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)

sse_bp = Blueprint("sse",__name__)

def getUser():
    user_id = get_jwt_identity()
    return f"user:{user_id}"
    
@sse_bp.route("/stream")
@jwt_required()
def stream():
    user_id = getUser()
    def events():
        last_id = "0"
        while True:
            result = redis_client.xread(
                {user_id:last_id}
            )
            for stream, messages in result:
                for message_id, data in messages:
                    last_id = message_id
                    print("Sending:", data["message"])
                    yield f"data: {data['message']}\n\n"
        return Response(
            events(),
            mimetype = "text/event-stream"
        )
        
    
