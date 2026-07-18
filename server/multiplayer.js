// Servidor multijugador de SKATE DEL TEMPLO — relevo de estados por WebSocket.
// Sin fisica en servidor: cada cliente simula su skater y aqui solo se
// reenvia {posicion, rotacion, clip} a los demas jugadores del mundo.
//
//   npm run mp        (puerto 8124; MP_PORT para cambiarlo)
//
const { WebSocketServer } = require('ws');

const PORT = process.env.MP_PORT || 8124;
const wss = new WebSocketServer({ port: PORT });

let nextId = 1;
const players = new Map(); // id -> {ws, name, state}

function send(ws, obj) {
  if (ws.readyState === 1) ws.send(JSON.stringify(obj));
}
function broadcast(obj, exceptId) {
  const msg = JSON.stringify(obj);
  for (const [id, p] of players) {
    if (id !== exceptId && p.ws.readyState === 1) p.ws.send(msg);
  }
}

wss.on('connection', (ws) => {
  let myId = null;

  ws.on('message', (raw) => {
    let m;
    try { m = JSON.parse(raw); } catch { return; }

    if (m.t === 'join' && myId === null) {
      myId = nextId++;
      const name = String(m.name || 'skater').slice(0, 16);
      players.set(myId, { ws, name, state: m.state || null });
      // al nuevo: su id + quienes ya estan
      send(ws, { t: 'welcome', id: myId,
        players: [...players].filter(([id]) => id !== myId)
          .map(([id, p]) => ({ id, name: p.name, state: p.state })) });
      // a los demas: entro alguien
      broadcast({ t: 'join', id: myId, name }, myId);
      console.log(`[+] ${name} (#${myId}) — ${players.size} en linea`);
    }

    if (m.t === 's' && myId !== null) {           // estado de movimiento
      const p = players.get(myId);
      if (p) p.state = m.d;
      broadcast({ t: 's', id: myId, d: m.d }, myId);
    }
  });

  ws.on('close', () => {
    if (myId !== null && players.delete(myId)) {
      broadcast({ t: 'leave', id: myId });
      console.log(`[-] #${myId} salio — ${players.size} en linea`);
    }
  });
  ws.on('error', () => {});
});

console.log(`SKATE DEL TEMPLO multijugador en ws://localhost:${PORT}`);
