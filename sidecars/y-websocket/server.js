const http = require('http');
const WebSocket = require('ws');
const Redis = require('ioredis');
const { setupWSConnection } = require('y-websocket/bin/utils');

const PORT = process.env.PORT || 1234;
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';

const redis = new Redis(REDIS_URL);
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('EduMeet Yjs WebSocket Server Running\n');
});

const wss = new WebSocket.Server({ noServer: true });

server.on('upgrade', async (request, socket, head) => {
  try {
    const url = new URL(request.url, `http://${request.headers.host}`);
    const ticket = url.searchParams.get('ticket');

    if (!ticket) {
      socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
      socket.destroy();
      return;
    }

    // Atomically consume single-use ticket from Redis
    const ticketKey = `ws_ticket:${ticket}`;
    const ticketPayload = await redis.getdel(ticketKey);

    if (!ticketPayload) {
      socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
      socket.destroy();
      return;
    }

    const { user_id, session_id, role } = JSON.parse(ticketPayload);
    request.user_id = user_id;
    request.session_id = session_id;
    request.role = role;

    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  } catch (err) {
    console.error('Error during WS upgrade authentication:', err);
    socket.write('HTTP/1.1 500 Internal Server Error\r\n\r\n');
    socket.destroy();
  }
});

wss.on('connection', (conn, req) => {
  // Bind connection to Yjs document named after the session_id
  const docName = `session_${req.session_id}`;
  setupWSConnection(conn, req, { docName, gc: true });
  console.log(`[y-websocket] User ${req.user_id} connected to document ${docName}`);
});

server.listen(PORT, () => {
  console.log(`[y-websocket] Server listening on port ${PORT}`);
});
