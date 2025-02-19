
#ifndef __RINGBUF16__
#define __RINGBUF16__

#include "ringbuf_generic.h"

typedef uint16_t RINGBUF16_DATA;

typedef volatile struct {
    volatile RINGBUF16_DATA *data;
    uint32_t mask;
    uint32_t start;
    uint32_t end;
} RINGBUF16;


static inline bool ringbuf16_initialize(
        RINGBUF16 *r,
        volatile RINGBUF16_DATA *buffer,
        uint32_t size)
{
	ring_init(r, buffer, size);
    return true;
}

static inline uint32_t ringbuf16_put(
        RINGBUF16 *r,
        volatile RINGBUF16_DATA *data,
        uint32_t dataLength)
{
	ring_put(r, data, dataLength);
}

static inline uint32_t ringbuf16_get(
        RINGBUF16 *r,
        volatile RINGBUF16_DATA *output_data_buffer,
        uint32_t output_data_buffer_size)
{
	ring_get(r, output_data_buffer, output_data_buffer_size);
}

static inline uint32_t ringbuf16_size(RINGBUF16 *r)
{
	ring_gaurd(r);
    return ring_size(r);
}

static inline uint32_t ringbuf16_pendingLength(RINGBUF16 *r)
{
	ring_gaurd(r);
	return ring_pending(r);
}

static inline uint32_t ringbuf16_availableLength(RINGBUF16 *r)
{
	ring_gaurd(r);
    return ring_available(r);
}


#endif // __RINGBUF16__
