
#ifndef __RINGBUF32__
#define __RINGBUF32__

#include "ringbuf_generic.h"

typedef uint32_t RINGBUF32_DATA;

typedef volatile struct {
    volatile RINGBUF32_DATA *data;
    uint32_t mask;
    uint32_t start;
    uint32_t end;
} RINGBUF32;


static inline bool ringbuf32_initialize(
        RINGBUF32 *r,
        volatile RINGBUF32_DATA *buffer,
        uint32_t size)
{
	ring_init(r, buffer, size);
    return true;
}

static inline uint32_t ringbuf32_put(
        RINGBUF32 *r,
        volatile RINGBUF32_DATA *data,
        uint32_t dataLength)
{
	ring_put(r, data, dataLength);
}

static inline uint32_t ringbuf32_get(
        RINGBUF32 *r,
        volatile RINGBUF32_DATA *output_data_buffer,
        uint32_t output_data_buffer_size)
{
    ring_get(r, output_data_buffer, output_data_buffer_size);
}

static inline int ringbuf32_size(RINGBUF32 *r)
{
	ring_gaurd(r);
    return ring_size(r);
}

static inline uint32_t ringbuf32_pendingLength(RINGBUF32 *r)
{
	ring_gaurd(r);
	return ring_pending(r);
}

static inline uint32_t ringbuf32_availableLength(RINGBUF32 *r)
{
	ring_gaurd(r);
    return ring_available(r);
}


#endif // __RINGBUF32__
