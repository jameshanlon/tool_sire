#include <xs1.h>
#include "util.h"
#include "definitions.h"

// Create a channel resource identifier with a particular count
//static inline
unsigned chanResId(unsigned id, int counter) {
    return destResId(id) | counter << 8;    
}

// Generate a configuration resource identifier
//static inline
unsigned genCRI(unsigned nodeId) {
    return nodeId << 24 | XS1_CT_SSCTRL << 8 | 12;
}

// Raise an exception in the event of an error
//static inline
void raiseException() {
    asm("ldc r11, 0\n\tecallf r11" ::: "r11");
}

// Exception error
//static inline
void error() {
    asm("waiteu");
}

// Get the id of this thread
unsigned getThreadId() {
    unsigned threadId;
    asm("get r11, id\n\t"
        "mov %0, r11" : "=r"(threadId) :: "r11");
    return threadId;
}

// Given a resource id, return the node identifer
unsigned getNode(unsigned resId) {
    unsigned int n;
    asm("bitrev %0, %1" : "=r"(n) : "r"(resId));
    return n & 0xFF;
}

// Given a resource id, return the core label. I.e. not separate node and core
// values
unsigned getCore(unsigned resId) {
    unsigned int n, c;
    asm("bitrev %0, %1" : "=r"(n) : "r"(resId));
    n &= 0xFF;
    c = (resId >> 16) & 0xFF;
    return (n * CORES_PER_NODE) + c;
}

// Create the channel identifier (for channel 0) for a given destination
// The node bits are written in MSB first, so need to be reversed
unsigned destResId(unsigned dest) {
    unsigned n = dest/CORES_PER_NODE;
    asm("bitrev %0, %1" : "=r"(n) : "r"(n));
    return n | (dest % CORES_PER_NODE) << 16 | 0x2;
}

/*static inline
int TESTCT(unsigned c) {
   int r;
   asm("testct %0, res[%1]" : "=r"(r) : "r"(c));
   return r;
}

static inline
void OUTCT_END(unsigned c) {
   asm("outct res[%0], %1" :: "r"(c), "r"(CT_END));
}

static inline
void CHKCT_END(unsigned c) {
   asm("chkct res[%0], %1" :: "r"(c), "r"(CT_END));
}

static inline
void SETD(unsigned c, unsigned dest) {
   asm("setd res[%0], %1" :: "r"(c), "r"(dest));
}

static inline
unsigned GETR_CHANEND() {
   unsigned c;
   asm("getr %0, 2":"=r"(c));
   return c;
}*/

