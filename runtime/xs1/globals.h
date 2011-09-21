// Copyright (c) 2011, James Hanlon, All rights reserved
// This software is freely distributable under a derivative of the
// University of Illinois/NCSA Open Source License posted in
// LICENSE.txt and at <http://github.xcore.com/>

#ifndef GLOBALS_H
#define GLOBALS_H

#include "system/xs1/definitions.h"

// Seperate master and slave versions
extern unsigned _sizetab[SIZE_TABLE_SIZE];

// External functions
extern void exceptionHandler();
extern void _main(void);

/* These variables are declared in globals.c. */

// Global data
extern unsigned _sp;
extern unsigned _seed;

/* Processor allocation ================================*/

// CRI of control spawn channel
extern unsigned spawn_master; 
extern unsigned thread_chans[MAX_THREADS];

/* Connection setup and management =====================*/

// Master-slave connection request record.
typedef struct
{ int connId;
  int origin;
  unsigned chanCRI;
} conn_req;

// Open server channel connection record.
typedef struct
{ int connId;
  unsigned chanCRI;
} conn_srv;

// CRI of control connection channel
extern unsigned conn_master; 
extern conn_req conn_buffer[CONN_BUFFER_SIZE];
extern conn_req conn_locals[MAX_THREADS];
extern conn_srv conn_server[MAX_OPEN_CONNS];

#endif

