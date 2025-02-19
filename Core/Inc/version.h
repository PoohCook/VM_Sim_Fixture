
#ifndef __STM_VERSION__
#define __STM_VERSION__

#include <stdint.h>

/**
 * Versioning is as follows:
 *  major.minor.[maintenance.[build]]
 */
#define _STM_VERSION_MAJOR           1
#define _STM_VERSION_MINOR           1
#define _STM_VERSION_MAINTENANCE     0
#define _STM_VERSION_BUILD           1

#define STM_VERSION_MAJOR           (uint8_t)_STM_VERSION_MAJOR
#define STM_VERSION_MINOR           (uint8_t)_STM_VERSION_MINOR
#define STM_VERSION_MAINTENANCE     (uint8_t)_STM_VERSION_MAINTENANCE
#define STM_VERSION_BUILD           (uint8_t)_STM_VERSION_BUILD

typedef struct {
    uint8_t major;
    uint8_t minor;
    uint8_t maintenance;
    uint8_t build;
} __attribute__((packed)) FIXTURE_VERSION;

FIXTURE_VERSION version_data();

#endif // __STM_VERSION__
