#ifndef __TICKS_HELPERS__
#define __TICKS_HELPERS__

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>



#define TICK_COUNT_MAX  0xffffffff
static inline TickType_t __diffTickCount(TickType_t start, TickType_t stop){
	if(stop >= start){
		return stop - start;
	}else{
		// wrap condition
		return  TICK_COUNT_MAX + stop - start;
	}
}

typedef struct{
	TickType_t start;
	TickType_t timeout;
} ACTIVITY_TIMER;

#define __activity_guard(t) { if((t) == NULL) return false; }
#define __currentTickDelta(t) (__diffTickCount((t)->start, xTaskGetTickCount()))

static inline bool activity_initialize( ACTIVITY_TIMER* t, TickType_t timeout){
	__activity_guard(t);
	t->start = xTaskGetTickCount();
	t->timeout =timeout;

	return true;
}

static inline bool activity_refresh( ACTIVITY_TIMER* t){
	__activity_guard(t);
	t->start = xTaskGetTickCount();

	return true;
}

static inline bool activity_expire( ACTIVITY_TIMER* t){
	__activity_guard(t);
	t->start = xTaskGetTickCount() - t->timeout;

	return true;
}

static inline bool activity_isExpired( ACTIVITY_TIMER* t){
	__activity_guard(t);

	return __currentTickDelta(t) >= t->timeout;
}




#endif // __TICKS_HELPERS__
