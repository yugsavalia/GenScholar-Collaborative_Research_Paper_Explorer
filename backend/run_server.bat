@echo off
echo Starting Django server with Daphne for WebSocket support...
daphne -b 0.0.0.0 -p 8000 cursortest.asgi:application



