
#ifndef LOGGING_H
#define LOGGING_H

//#define DEBUG

#define LOG_BUFFER_MAX_SIZE 490

void log_message_out( const char* level, const char * format, ... );

// #define DETAILED_LOGS
#ifdef DETAILED_LOGS
    #define LOG_INFO(...)   log_message_out(KERN_INFO,  __VA_ARGS__)
    #define LOG_WARN(...)   log_message_out(KERN_WARNING, __VA_ARGS__ )
    #define LOG_ERROR(...)  log_message_out(KERN_ERR,  __VA_ARGS__)
    #ifdef DEBUG
    #define LOG_DEBUG(...)  log_message_out(KERN_INFO, __VA_ARGS__)
    #else
    #define LOG_DEBUG(...)
    #endif
#else
    #define LOG_INFO(...)
    #define LOG_WARN(...)
    #define LOG_ERROR(...)
    #ifdef DEBUG
    #define LOG_DEBUG(...)
    #else
    #define LOG_DEBUG(...)
    #endif
#endif

#endif //LOGGING_H
