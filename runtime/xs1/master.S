// Copyright (c) 2011, James Hanlon, All rights reserved
// This software is freely distributable under a derivative of the
// University of Illinois/NCSA Open Source License posted in
// LICENSE.txt and at <http://github.xcore.com/>

#include <xs1.h>
#include "system/xs1/definitions.h"

  .extern touchRegs
  .extern initMemory
  .extern initPointers
  .extern resetChanends
  .extern initThreads
  .extern initChanends
  .extern initPorts
  .extern initConnections
  .extern initJumpTable
  .extern masterSync
  .extern initMaster
  .extern hostHandler
  .extern connHandler
  .extern controlIdle
  
  .extern spawn_master
  .extern conn_master
  .extern _numProgEntries
  .extern _jumpLocations

  .globl main
  .globl _start
  .globl _master,       "f{0}(0)"
  .globl setInterrupts, "f{0}(0)"
  .globl runMain,       "f{0}(ui)"

  .text

/*============================================================================
 * This initialises the execution of thread 0, core 0
 *==========================================================================*/
  .cc_top _master.function, _master 
  .align 2 

main:
_start:
_master:
  
  bl touchRegs
  bl initMemory
  bl initPointers
  bl setupTraps
  bl resetChanends
  bl initJumpTable
  bl initThreads
  bl initChanends
  bl initPorts
  bl initConnections
  bl initJumpTable
  bl __alloc_libc_hwlock
  bl setInterrupts
  bl masterSync
  
  bl initMain
  bu controlIdle

  .cc_bottom _master.function

/*===========================================================================
 * Set interrupts for the master control thread (thread 0, core 0). This is 
 * for both the spawn channel and the connection channel. Thread 0 on core 0 
 * will always be busy so it will always be interrupted and never in an idle 
 * state.
 *==========================================================================*/
  .cc_top setInterrupts.function, setInterrupts
  .align 2 
   
setInterrupts:
  entsp 2
  stw r11, sp[0]
  stw r10, sp[1]

  /* Set spawn_master event vector = &hostHandler
  and Set spawn_master channel mode to interrupts. */
  ldap r11, hostHandler
  ldw  r10, dp[spawn_master]
  setv res[r10], r11
  setc res[r10], XS1_SETC_IE_MODE_INTERRUPT
  
  /* Set conn_master event vector = &connHandler
  and Set conn_master channel mode to interrupts. */
  ldap r11, connHandler
  ldw  r10, dp[conn_master]
  setv res[r10], r11
  setc res[r10], XS1_SETC_IE_MODE_INTERRUPT
  
  /* Enable interrupts */
  setsr SR_IEBLE
  
  ldw r11, sp[0]
  ldw r10, sp[1]
  retsp 2

  .cc_bottom setInterrupts.function

/*==============================================================
 * Initiliase the jump table with the program entries. 
 *============================================================*/
.cc_top initJumpTable.function, initJumpTable
.align 2
initJumpTable:
	ldaw r11, cp[_jumpTable]
  mov  r10, r11
  ldaw r11, dp[_jumpLocations]
  mov  r9, r11
  ldw  r8, dp[_numProgEntries]
  ldc  r7, 0
_loop:
  lss  r11, r7, r8
  bf   r11, _exit
  ldw  r11, r9[r7]
  ldc  r6, JUMP_INDEX_OFFSET
  add  r6, r7, r6
  stw  r11, r10[r6]
  add  r7, r7, 1
  bu   _loop
_exit:

	retsp 0
.cc_bottom initJumpTable.function

/*==============================================================
 * A wrapper to run the program main so that r0-r3 are preserved 
 * properly.
 *============================================================*/
  .cc_top runMain.function, runMain
  .align 2 
   
runMain:
  entsp 1
  bla r0
  retsp 1

  .cc_bottom runMain.function

