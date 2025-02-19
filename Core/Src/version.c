/*
 * File:   Version.c
 * Author: Pooh
 *
 * Created on July 19, 2023
 */

#include "version.h"
#include "main.h"


FIXTURE_VERSION version_data(){

    //     /* Get the version */
    FIXTURE_VERSION version = {
        .major = STM_VERSION_MAJOR,
        .minor = STM_VERSION_MINOR,
        .maintenance = STM_VERSION_MAINTENANCE,
        .build = STM_VERSION_BUILD
    };

    return version;
}
