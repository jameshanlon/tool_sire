// Copyright (c) 2011, James Hanlon, All rights reserved
// This software is freely distributable under a derivative of the
// University of Illinois/NCSA Open Source License posted in
// LICENSE.txt and at <http://github.xcore.com/>

#include <xs1.h>
#include "system/xs1/definitions.h"
#include "system/definitions.h"
#include "globals.h"
#include "system.h"
#include "util.h"
#include "host.h"

// In host.S:
extern void runProcess(int procIndex, unsigned int args[], int numArgs);

void       initSourceConnection(unsigned, unsigned);
{int, int} receiveClosure     (unsigned, int[], unsigned[], int[]);
{int, int} receiveHeader      (unsigned);
void       receiveArguments   (unsigned, int, int[], unsigned[], int[]);
int        receiveProcedures  (unsigned, int);
void       informCompleted    (unsigned, unsigned);
void       sendResults        (unsigned, int, int[], unsigned[], int[]);

/*
 * Setup and initialise execution of a new thread.
 */
void runThread(unsigned senderId) {
  int procIndex;
  int numArgs;
  int argTypes[MAX_PROC_PARAMETERS];
  unsigned argValues[MAX_PROC_PARAMETERS];
  int argLengths[MAX_PROC_PARAMETERS];
  unsigned threadId;
  THREAD_ID(threadId);
  
  // Initialise connection with sender
  initSourceConnection(thread_chans[threadId], senderId);
  
  // Receive closure data
  {procIndex, numArgs} = receiveClosure(thread_chans[threadId], 
      argTypes, argValues, argLengths);

  // Run the process
  runProcess(procIndex, argValues, numArgs);

  // Complete the creation by sending back any results
  informCompleted(thread_chans[threadId], senderId);
  
  // Send any results back
  sendResults(thread_chans[threadId], numArgs, argTypes, argValues, argLengths);
}

/*
 * Initialise source connection with this thread 0 as host.
 */
unsigned setHost() {
  unsigned senderId;
  
  // Connect to the sender and receive their id 
  IN(spawn_master, senderId);
  SETD(spawn_master, senderId);
  
  // Close spawn_master connection
  OUTCT_END(spawn_master);
  CHKCT_END(spawn_master);

  return senderId;
}

/* 
 * Host an incoming procedure when thread 0 is BUSY. During this time, events
 * and interrupts are disabled and more requests may be made but they will not
 * arrive until the spawn_master channel connection is closed.
 */
void spawnHost() {
  unsigned senderId;
  unsigned pc;
  
  // Connect to the sender and receive their id 
  IN(spawn_master, senderId);
  SETD(spawn_master, senderId);

  // Close the connection
  CHKCT_END(spawn_master);
  OUTCT_END(spawn_master);

  // Give the next thread some space and launch it
  asm volatile("ldap r11, runThread ; mov %0, r11" : "=r"(pc) :: "r11");
  newAsyncThread(pc, senderId, 0, 0, 0);
}

/*
 * Initialise the conneciton with the sender. Communication performed on a
 * slave spawn channel.
 */
void initSourceConnection(unsigned c, unsigned senderId) {
  
  // Send the new CRI
  SETD(c, senderId);
  OUT(c, c);

  // Sync and close the conncection
  OUTCT_END(c);
  CHKCT_END(c);
}

/*
 * Receive a closure.
 */
#pragma unsafe arrays
{int, int} receiveClosure(unsigned c, 
    int argTypes[], unsigned argValues[], int argLengths[]) {
  
  int numArgs, numProcs, index;

  // Receive the header
  {numArgs, numProcs} = receiveHeader(c);

  // Receive arguments
  receiveArguments(c, numArgs, argTypes, argValues, argLengths);

  // Receive the children
  index = receiveProcedures(c, numProcs);

  return {index, numArgs};
}

/*
 * Receive the closure header.
 */
{int, int} receiveHeader(unsigned c) {
  int numArgs;
  int numProcs; 
  INS(c, numArgs);
  INS(c, numProcs);
  return {numArgs, numProcs};
}

/*
 * Receive the arguments to the new procedure.
 */
#pragma unsafe arrays
void receiveArguments(unsigned c, int numArgs, 
    int argTypes[], unsigned argValues[], int argLengths[]) {

  // For each argument
  for(int i=0; i<numArgs; i++) {

    // Receive the argument type
    INS(c, argTypes[i]);

    switch(argTypes[i]) {
    default: break;
    
    case t_arg_ALIAS:
      INS(c, argLengths[i]);
      argValues[i] = memAlloc(argLengths[i]*BYTES_PER_WORD);
      
      // Receive each element of the array and write straight to memory
      for(int j=0; j<argLengths[i]; j++) {
        unsigned value;
        INS(c, value);
        asm volatile("stw %0, %1[%2]" :: "r"(value), "r"(argValues[i]), "r"(j));
      }
      break;
    
    case t_arg_VAR:
      argLengths[i] = 1;
      argValues[i] = memAlloc(BYTES_PER_WORD);
      {unsigned value;
      INS(c, value);
      asm volatile("stw %0, %1[%2]" :: "r"(value), "r"(argValues[i]), "r"(0));}
      break;
    
    case t_arg_CHANEND:
      argLengths[i] = 1;
      INS(c, argValues[i]);
      break;
    
    case t_arg_VAL:
      argLengths[i] = 1;
      INS(c, argValues[i]);
      break;
    }
  }
}

/*
 * Receive the procedure and any children.
 */
#pragma unsafe arrays
int receiveProcedures(unsigned c, int numProcs) {
  int index;
  unsigned jumpTable;

  // Load jump table address
  asm volatile("ldaw r11, cp["LABEL_JUMP_TABLE"] ; mov %0, r11" : "=r"(jumpTable) :: "r11");

  for(int i=0; i<numProcs; i++) {
    
    // Jump index and size
    int procIndex;
    INS(c, procIndex);
    if(i == 0) index = procIndex;

    // If we don't have the procedure, receive it
    if (SIZE_TABLE[procIndex] == 0) {
      
      int procSize;
      unsigned ptr;
      
      OUTS(c, 1);
      INS(c, procSize);
      ptr = memAlloc(procSize);

      // Instructions
      for(int j=0; j<procSize/4; j++) {
        unsigned inst;
        INS(c, inst);
        asm volatile("stw %0, %1[%2]" :: "r"(inst), "r"(ptr), "r"(j));
      }
     
      // Patch jump table entry
      asm volatile("stw %0, %1[%2]" :: "r"(ptr), "r"(jumpTable), "r"(procIndex));

      // Update the procSize entry
      SIZE_TABLE[procIndex] = procSize;
    }
    else {
      OUTS(c, 0);
    }
  }

  return index;
}

/* 
 * Complete the migration of the procedure by informing the sender and
 * transmitting back any results.
 */
void informCompleted(unsigned c, unsigned senderId) {
  
  // Set the channel destination (as it may have been set again by a nested on)
  SETD(c, senderId);

  // Signal the completion of execution
  asm volatile("outct res[%0], " S(CT_COMPLETED) :: "r"(c));
  asm volatile("chkct res[%0], " S(CT_COMPLETED) :: "r"(c));
  
  // End
  OUTCT_END(c);
  CHKCT_END(c);
}

/*
 * Send back any arrays that may have been updated by the execution of
 * the migrated procedure.
 */
#pragma unsafe arrays
void sendResults(unsigned c, int numArgs, 
    int argTypes[], unsigned argValues[], int argLengths[]) {
  unsigned value;
  
  for(int i=0; i<numArgs; i++) {
    
    switch(argTypes[i]) {
    default: break;
    
    case t_arg_ALIAS:
      for(int j=0; j<argLengths[i]; j++) {
        asm volatile("ldw %0, %1[%2]" : "=r"(value) : "r"(argValues[i]), "r"(j));
        OUTS(c, value);
      }
      memFree(argValues[i]);
      break;
    
    case t_arg_VAR:
      asm volatile("ldw %0, %1[%2]" : "=r"(value) : "r"(argValues[i]), "r"(0));
      OUTS(c, value);
      memFree(argValues[i]);
      break;
   
    case t_arg_CHANEND:
      break;

    case t_arg_VAL:
      break;
    }
  }
}

