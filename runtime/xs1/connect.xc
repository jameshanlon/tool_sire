#include <print.h>

#include "util.h"
#include "globals.h"
#include "connect.h"

#define LOCAL_CONNECT_CHAN(c, resID) \
do { \
  CHAN_RI(0, CHAN_ID_CONTROL_CONNECT, resID); \
  resID = ((c & 0xFFFF0000) | (resID & 0xFFFF)); \
} while(0)
#define COMPLETE(c, cri, v) \
do { \
  SETD(c, cri); \
  OUT(c, v); \
  OUTCT_END(c); \
} while(0)
#define NONE (-1)

typedef enum {
  MASTER = 0,
  SLAVE = 1,
  SERVER = 2,
  CLIENT = 3
} ReqType;

// Master-slave connection handling
bool dequeueMasterReq(conn_req &r, int connId, int origin);
bool dequeueSlaveReq(conn_req &r, int connId, int origin);
void queueMasterReq(int connId, int origin, unsigned chanCRI);
void queueSlaveReq(unsigned tid, int connId, int origin, unsigned chanCRI);

// Client-server conneciton handling
void openConn(int connId, unsigned chanCRI);
bool getOpenConn(conn_srv &c, int connId);
void queueClientReq(int connId, unsigned chanCRI);
bool dequeueClientReq(conn_req &r, int connId);

/*
 * Initialise the conn_buffer and conn_local arrays.
 */
#pragma unsafe arrays
void initConnections()
{ for (int i=0; i<CONN_BUFFER_SIZE; i++)
    conn_buffer[i].connId = NONE;
  for (int i=0; i<MAX_THREADS; i++)
    conn_locals[i].connId = NONE;
  for (int i=0; i<MAX_OPEN_CONNS; i++)
    conn_server[i].connId = NONE;
}

/*
 * Master connection protocol:
 *  0. Get a new channel c and construct target CRI (conn_master).
 *  1. Output channel id on (separate) thread channel t.
 *  2. Output CRI on t.
 *  3. Input slave CRI on t.
 *  4. Set local channel destination of c and return it.
 */
unsigned _connectMaster(int connId, int dest)
{ unsigned c;
  unsigned destCRI;
  CHAN_RI(dest, CHAN_ID_CONTROL_CONNECT, destCRI);
  GETR_CHANEND(c);
  SETD(c, destCRI);
  
  OUT(c, c);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, MASTER);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, connId);
  OUTCT_END(c);
  CHKCT_END(c);

  IN(c, destCRI);
  CHKCT_END(c);
  SETD(c, destCRI);
  return c;
}

/*
 * Slave connection protocol:
 *  0. Get a new channel c and construct (local) dest CRI (conn_master).
 *  1. Output thread id on (separate) thread channel t.
 *  2. Output channel id on t.
 *  3. Output CRI on t.
 *  4. Input master CRI on t.
 *  5. Set local channel destination of c and return it.
 */
unsigned _connectSlave(int connId, int origin)
{ unsigned c;
  unsigned destCRI;
  unsigned threadID;
  GETR_CHANEND(c);
  LOCAL_CONNECT_CHAN(c, destCRI);
  SETD(c, destCRI);
  
  OUT(c, c);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, SLAVE);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, connId);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, origin);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  THREAD_ID(threadID);
  OUT(c, threadID);
  OUTCT_END(c);
  CHKCT_END(c);
  
  IN(c, destCRI);
  CHKCT_END(c);
  SETD(c, destCRI);
  return c;
}

/*
 * Open a server connection for clients to connect to.
 */
unsigned _connectServer(int connId)
{ unsigned c;
  unsigned destCRI;
  GETR_CHANEND(c);
  LOCAL_CONNECT_CHAN(c, destCRI);
  SETD(c, destCRI);
  
  OUT(c, c);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, SERVER);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, connId);
  OUTCT_END(c);
  CHKCT_END(c);
  return c;
}

/*
 * Connect a client to an open server connection.
 */
unsigned _connectClient(int connId, int dest)
{ unsigned c;
  unsigned destCRI;
  CHAN_RI(dest, CHAN_ID_CONTROL_CONNECT, destCRI);
  GETR_CHANEND(c);
  SETD(c, destCRI);
  
  OUT(c, c);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, CLIENT);
  OUTCT_ACK(c);
  CHKCT_ACK(c);
  
  OUT(c, connId);
  OUTCT_END(c);
  CHKCT_END(c);

  IN(c, destCRI);
  CHKCT_END(c);
  SETD(c, destCRI);
  return c;
}

/*
 * Handle an incoming master or slave connection request.
 *
 * Thread 0 serve master connection request.
 *  1. Receive channel id
 *  2. Receive address of master (origin)
 *  3. Receive master CRI
 *  [queue or complete]
 *
 * Thread 0 serve slave connection request.
 *  1. Receive slave thread id
 *  2. Receive channel id
 *  3. Receive master address (origin)
 *  4. Receive slave CRI
 *  [queue or complete]
 *
 * Or a server or client request.
 */
void serveConnReq()
{ ReqType type;
  unsigned chanCRI;
  IN(conn_master, chanCRI);
  CHKCT_ACK(conn_master);
  SETD(conn_master, chanCRI);
  OUTCT_ACK(conn_master);
  
  IN(conn_master, type);
  CHKCT_ACK(conn_master);
  OUTCT_ACK(conn_master);
  
  switch (type)
  { default: 
      ASSERT(0); 
      break;
    case MASTER:
      { conn_req sReq; 
        int origin;
        int connId;
        IN(conn_master, connId);
        CHKCT_END(conn_master);
        OUTCT_END(conn_master);
        GET_GLOBAL_CORE_ID(chanCRI, origin);
        if (!dequeueSlaveReq(sReq, connId, origin))
          queueMasterReq(connId, origin, chanCRI);
        else
        { COMPLETE(conn_master, chanCRI, sReq.chanCRI);
          COMPLETE(conn_master, sReq.chanCRI, chanCRI);
        }
      }
      break;
    case SLAVE:
      { conn_req mReq;
        int origin;
        int tid;
        int connId;
        IN(conn_master, connId);
        CHKCT_ACK(conn_master);
        OUTCT_ACK(conn_master);
        IN(conn_master, origin);
        CHKCT_ACK(conn_master);
        OUTCT_ACK(conn_master);
        IN(conn_master, tid);
        CHKCT_END(conn_master);
        OUTCT_END(conn_master);
        if (!dequeueMasterReq(mReq, connId, origin))
          queueSlaveReq(tid, connId, origin, chanCRI);
        else
        { COMPLETE(conn_master, mReq.chanCRI, chanCRI);
          COMPLETE(conn_master, chanCRI, mReq.chanCRI);
        }
      }
      break;
    case SERVER:
      { conn_req cReq;
        int connId;
        IN(conn_master, connId);
        CHKCT_END(conn_master);
        OUTCT_END(conn_master);
        openConn(connId, chanCRI);
        // Complete each client waiting on this connection id
        while (dequeueClientReq(cReq, connId)) 
        { SETD(conn_master, cReq.chanCRI);
          OUT(conn_master, chanCRI);
          OUTCT_END(conn_master);
        }
      }
      break;
    case CLIENT:
      { conn_srv cOpen;
        int connId;
        IN(conn_master, connId);
        CHKCT_END(conn_master);
        OUTCT_END(conn_master);
        if (getOpenConn(cOpen, connId)) {
          OUT(conn_master, cOpen.chanCRI);
          OUTCT_END(conn_master);
        }
        else
          queueClientReq(connId, chanCRI);
      }
      break;
  }
}

/*
 * Dequeue a master connection request matching the channel id.
 */
bool dequeueMasterReq(conn_req &r, int connId, int origin)
{ for (int i=0; i<CONN_BUFFER_SIZE; i++)
  { if (conn_buffer[i].connId == connId 
      && conn_buffer[i].origin == origin)
    { conn_buffer[i].connId = NONE;
      r.chanCRI = conn_buffer[i].chanCRI;
      return true;
    }
  }
  return false;
}

/*
 * Dequeue a slave connection request.
 */
bool dequeueSlaveReq(conn_req &r, int connId, int origin)
{ for (int i=0; i<MAX_THREADS; i++)
  { if (conn_locals[i].connId == connId
      && conn_locals[i].origin == origin)
    { conn_locals[i].connId = NONE;
      r.chanCRI = conn_locals[i].chanCRI;
      return true;
    }
  }
  return false;
}

/*
 * Queue a master connection request: insert it in the next available slot in
 * the buffer.
 */
void queueMasterReq(int connId, int origin, unsigned chanCRI)
{ for (int i=0; i<CONN_BUFFER_SIZE; i++)
  { if (conn_buffer[i].connId == NONE)
    { conn_buffer[i].connId = connId;
      conn_buffer[i].origin = origin;
      conn_buffer[i].chanCRI = chanCRI;
      return;
    }
  }
  ASSERT(0);
}

/*
 * Queue a slave connection request: insert it in the slot given by the thread
 * id.
 */
void queueSlaveReq(unsigned tid, int connId, int origin, unsigned chanCRI)
{ conn_locals[tid].connId = connId;
  conn_locals[tid].origin = origin;
  conn_locals[tid].chanCRI = chanCRI;
}

/*
 * Open a server connection.
 */
void openConn(int connId, unsigned chanCRI)
{ for (int i=0; i<MAX_OPEN_CONNS; i++)
  { if (conn_server[i].connId == NONE)
    { conn_server[i].connId = connId;
      conn_server[i].chanCRI = chanCRI;
      return;
    }
  }
  ASSERT(0);
}

/*
 * Return the CRI of an open conneciton with a matching conneciton id.
 */
bool getOpenConn(conn_srv &c, int connId)
{ for (int i=0; i<MAX_OPEN_CONNS; i++)
  { if (conn_server[i].connId == connId)
    { c.connId = connId;
      c.chanCRI = conn_server[i].chanCRI;
      return true;
    }
  }
  return false;
}

/*
 * Queue a client conneciton request. This will occur only when a client tries
 * to connect to a server channel before it has opened.
 */
void queueClientReq(int connId, unsigned chanCRI)
{ for (int i=0; i<CONN_BUFFER_SIZE; i++)
  { if (conn_buffer[i].connId == NONE)
    { conn_buffer[i].connId = connId;
      conn_buffer[i].chanCRI = chanCRI;
      return;
    }
  }
  ASSERT(0);
}

/*
 * Dequeue and complete any outstanding client-to-server connection requests.
 */
bool dequeueClientReq(conn_req &r, int connId)
{ for (int i=0; i<CONN_BUFFER_SIZE; i++)
  { if (conn_buffer[i].connId == connId) 
    { conn_buffer[i].connId = NONE;
      r.connId = connId;
      r.chanCRI = conn_buffer[i].chanCRI;
      return true;
    }
  }
  return false;
}

