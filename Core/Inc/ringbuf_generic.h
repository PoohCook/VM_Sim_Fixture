#ifndef __RINGBUF_GENERIC__
#define __RINGBUF_GENERIC__

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

/*
 * general helper defines for all ring buffers
 */
#define ring_isPowerofTwo(x) (((x) & ((x) - 1)) == 0)
#define ring_min(a,b) (((a) < (b)) ? (a) : (b))
#define ring_size(r) ((r)->mask + 1)
#define ring_endToWrap(r) (ring_size((r)) - (r)->end)
#define ring_startToWrap(r) (ring_size((r)) - (r)->start - (r->end == 0 ? 1 : 0))  // if end at zero, must stop one short of wrap
#define ring_endToStart(r) ((r)->start - (r)->end)
#define ring_startToEnd(r) ((r)->end - (r)->start -1) // -1 accounts for not filling a ring to appear empty
#define ring_isWrapped(r) ((r)->start < (r)->end)
#define ring_gaurd(r) { if((r) == NULL) { return -1; } }
#define ring_pending(r) (((r)->start - (r)->end) & (r)->mask)
#define ring_available(r) (ring_size(r) - ring_pending(r) - 1)
#define ring_reset(r) { (r)->start = (r)->end = 0; }
#define ring_startDataPtr(r) ((uint8_t*)((r)->data + (r)->start))
#define ring_endDataPtr(r) ((uint8_t*)((r)->data + (r)->end))
#define ring_dataSize(r) (sizeof((r)->data[0]))
#define ring_incStart(r,i) {(r)->start = ((r)->start + (i)) & (r)->mask; }
#define ring_incEnd(r,i) {(r)->end = ((r)->end + (i)) & (r)->mask; }
#define ring_pendingContinuousLength(r) (ring_isWrapped((r)) ? ring_endToWrap((r)) : ring_endToStart((r)))
#define ring_availableContinuousLength(r) (ring_isWrapped((r)) ? ring_startToEnd((r)) : ring_startToWrap((r)))

#define ring_init(r,b,s) {\
	    if(r == NULL || b == NULL || !ring_isPowerofTwo(size)) return false;\
	    r->data = b;\
	    r->mask = s - 1;\
	    ring_reset((r));\
}\

#define ring_put(r,d,l) {\
	if(r == NULL || d == NULL || l < 0) return -1;\
    uint32_t i = 0;\
    while(i < (l)) {\
        uint32_t continuous_length = ring_min(ring_availableContinuousLength(r), (l) - i);\
        if(continuous_length <= 0) break;\
        memcpy(ring_startDataPtr((r)), (uint8_t*)((d) + i), continuous_length * ring_dataSize((r)));\
		ring_incStart(r,continuous_length);\
        i += continuous_length;\
    }\
    return i;\
}

#define ring_get(r,d,l) {\
    uint32_t i = 0;\
    while(i < (l)) {\
        uint32_t continuous_length = ring_min(ring_pendingContinuousLength((r)), (l) - i);\
        if(continuous_length <= 0) break; \
        memcpy((uint8_t*)((d) + i), ring_endDataPtr((r)), continuous_length * ring_dataSize((r)));\
		ring_incEnd(r,continuous_length);\
        i+= continuous_length;\
    }\
    return i;\
}




#endif  //  __RINGBUF_GENERIC__
