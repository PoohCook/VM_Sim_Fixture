
#ifndef __RINGBUF__
#define __RINGBUF__

#include "ringbuf_generic.h"

typedef uint8_t RINGBUF_DATA;

typedef volatile struct {
	volatile RINGBUF_DATA *data;
    uint32_t mask;
    uint32_t start;
    uint32_t end;
} RINGBUF;


static inline bool ringbuf_initialize(
        RINGBUF *r,
		volatile RINGBUF_DATA *buffer,
        uint32_t size)
{
	ring_init(r, buffer, size);
    return true;
}

static inline uint32_t ringbuf_put(
        RINGBUF *r,
		volatile RINGBUF_DATA *data,
        uint32_t dataLength)
{
	ring_put(r, data, dataLength);
}

static inline uint32_t ringbuf_get(
        RINGBUF *r,
		volatile RINGBUF_DATA *output_data_buffer,
        uint32_t output_data_buffer_size)
{
	ring_get(r, output_data_buffer, output_data_buffer_size);
}


static inline int ringbuf_size(RINGBUF *r)
{
	ring_gaurd(r);
    return ring_size(r);
}


static inline uint32_t ringbuf_pendingLength(RINGBUF *r)
{
	ring_gaurd(r);
	return ring_pending(r);

}

static inline uint32_t ringbuf_availableLength(RINGBUF *r)
{
	ring_gaurd(r);
    return ring_available(r);
}


#endif // __RINGBUF__
