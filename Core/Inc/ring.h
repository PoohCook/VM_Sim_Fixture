#ifndef _RING_HELPER_H
#define _RING_HELPER_H


/*
 * Ring buffer helpers
 */

#define _RING_INCR_HEAD(ring)   ((ring)->head = ((ring)->head + 1) & _RING_MASK)
#define _RING_INCR_TAIL(ring)   ((ring)->tail = ((ring)->tail + 1) & _RING_MASK)
#define _RING_HAS_NO_DATA(ring)  ((ring)->head == (ring)->tail)
#define _RING_IS_FULL(ring)  ((((ring)->head+1) & _RING_MASK) == (ring)->tail)
#define _RING_MAKE_EMPTY(ring)  ((ring)->head = (ring)->tail = 0)

#endif  //_RING_HELPER_H
