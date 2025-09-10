# import socketio
# from urllib.parse import parse_qs
# from logger import logger
# # 1. Create a Socket.IO server with async_mode set to 'asgi' (needed for FastAPI/Starlette).
# sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
# # 2. Create an ASGI application from Socket.IO server.
# socket_app = socketio.ASGIApp(sio)
# # 3. Define your Socket.IO event handlers below.
# # Bidirectional mappings
# user_socket_map = {}     # Maps userId -> socketId
# sid_to_user_id = {}      # Maps socketId -> userId
# active_calls = {}  # Maps callerUserId -> calleeUserId
# # ---------------------------
# # Socket.IO Event Handlers
# # ---------------------------
# @sio.event
# async def connect(sid, environ):
#     print(f"[Socket.IO] Client connected: {sid}")
#     # Parse query parameters
#     query_params = environ.get('asgi.scope', {}).get('query_string', b'').decode()
#     parsed_qs = parse_qs(query_params)
#     user_id = parsed_qs.get('id', [None])[0]
#     if user_id:
#         user_socket_map[user_id] = sid
#         sid_to_user_id[sid] = user_id
#         print(f"User ID {user_id} connected with SID {sid}")
#     else:
#         print(f"No User ID found for SID {sid}")
#     print(f"Connected users: {user_socket_map}")
# @sio.event
# async def disconnect(sid):
#     print(f"[Socket.IO] Client disconnected: {sid}")
#     user_id = sid_to_user_id.get(sid)
#     if user_id:
#         # Notify all peers that might be in a call with this user
#         # Iterate through active_calls to find any calls involving this user
#         calls_to_end = [caller for caller, callee in active_calls.items() if caller == user_id or callee == user_id]
#         for caller in calls_to_end:
#             callee = active_calls.get(caller)
#             if callee:
#                 callee_sid = user_socket_map.get(callee)
#                 if callee_sid:
#                     await sio.emit('call_disconnected', {
#                         "fromUserId": user_id
#                     }, room=callee_sid)
#                 del active_calls[caller]
#         # Remove from mappings
#         del sid_to_user_id[sid]
#         del user_socket_map[user_id]
#         print(f"User ID {user_id} disconnected")
#     else:
#         print(f"SID {sid} disconnected but no user_id was found")
#     print(f"Connected users: {user_socket_map}")
# @sio.event
# async def webrtc_offer(sid, data):
#     """
#     Receive an offer from one peer and send it to a specific peer.
#     `data` should include:
#     {
#         "targetUserId": "user123",
#         "sdp": "..."
#     }
#     """
#     target_user_id = str(data.get("targetUserId"))
#     sdp = data.get("sdp")
#     from_user_id = sid_to_user_id.get(sid, "unknown")
#     logger.info(f"webrtc_offer from {from_user_id} to {target_user_id}: {data}")
#     if target_user_id and sdp:
#         target_sid = user_socket_map.get(target_user_id)
#         if target_sid:
#             print(f"[Socket.IO] Sending OFFER from User ID {from_user_id} (SID: {sid}) to User ID {target_user_id} (SID: {target_sid})")
#             active_calls[from_user_id] = target_user_id
#             await sio.emit('webrtc_offer', {
#                 "fromUserId": from_user_id,
#                 "sdp": sdp
#             }, room=target_sid)
#         else:
#             print(f"[Socket.IO] Target User ID {target_user_id} not found")
#     else:
#         print(f"[Socket.IO] Invalid webrtc_offer data from SID {sid}: {data}")
# @sio.event
# async def webrtc_answer(sid, data):
#     """
#     Receive an answer from one peer and send it to a specific peer.
#     `data` should include:
#     {
#         "targetUserId": "user123",
#         "sdp": "..."
#     }
#     """
#     target_user_id = str(data.get("targetUserId"))
#     sdp = data.get("sdp")
#     from_user_id = sid_to_user_id.get(sid, "unknown")
#     if target_user_id and sdp:
#         target_sid = user_socket_map.get(target_user_id)
#         if target_sid:
#             print(f"[Socket.IO] Sending ANSWER from User ID {from_user_id} (SID: {sid}) to User ID {target_user_id} (SID: {target_sid})")
#             active_calls[from_user_id] = target_user_id
#             await sio.emit('webrtc_answer', {
#                 "fromUserId": from_user_id,
#                 "sdp": sdp
#             }, room=target_sid)
#         else:
#             print(f"[Socket.IO] Target User ID {target_user_id} not found")
#     else:
#         print(f"[Socket.IO] Invalid webrtc_answer data from SID {sid}: {data}")
# @sio.event
# async def webrtc_ice_candidate(sid, data):
#     """
#     Receive ICE candidate from one peer and send it to a specific peer.
#     `data` should include:
#     {
#         "targetUserId": "user123",
#         "candidate": {...}
#     }
#     """
#     target_user_id = str(data.get("targetUserId"))
#     candidate = data.get("candidate")
#     from_user_id = sid_to_user_id.get(sid, "unknown")
#     if target_user_id and candidate:
#         target_sid = user_socket_map.get(target_user_id)
#         if target_sid:
#             print(f"[Socket.IO] Sending ICE Candidate from User ID {from_user_id} (SID: {sid}) to User ID {target_user_id} (SID: {target_sid})")
#             await sio.emit('webrtc_ice_candidate', {
#                 "fromUserId": from_user_id,
#                 "candidate": candidate
#             }, room=target_sid)
#         else:
#             print(f"[Socket.IO] Target User ID {target_user_id} not found")
#     else:
#         print(f"[Socket.IO] Invalid webrtc_ice_candidate data from SID {sid}: {data}")
# @sio.event
# async def call_disconnect(sid, data):
#     """
#     Handle a call disconnect event.
#     `data` should include:
#     {
#         "targetUserId": "user123"
#     }
#     """
#     from_user_id = sid_to_user_id.get(sid, "unknown")
#     target_user_id = str(data.get("targetUserId"))
#     if from_user_id and target_user_id:
#         target_sid = user_socket_map.get(target_user_id)
#         if target_sid:
#             print(f"[Socket.IO] User ID {from_user_id} (SID: {sid}) has disconnected the call with User ID {target_user_id} (SID: {target_sid})")
#             # Notify the callee that the call has been disconnected
#             await sio.emit('call_disconnected', {
#                 "fromUserId": from_user_id
#             }, room=target_sid)
#             # Clean up the active_calls mapping
#             if from_user_id in active_calls:
#                 del active_calls[from_user_id]
#             if target_user_id in active_calls:
#                 del active_calls[target_user_id]
#         else:
#             print(f"[Socket.IO] Target User ID {target_user_id} not found for call_disconnect")
#     else:
#         print(f"[Socket.IO] Invalid call_disconnect data from SID {sid}: {data}")