import { Injectable } from '@angular/core';
import { LogContext } from '../interfaces/logging.interface';

@Injectable({
    providedIn: 'root'
  })
  export class LoggingService {
    private defaultContext: Partial<LogContext> = {
      user: 'Cliente',
      timestamp_utc: '2025-01-17 17:34:09'
    };
  
    private getContext(context: Partial<LogContext> = {}): LogContext {
      return {
        ...this.defaultContext,
        ...context,
        user: context.user || this.defaultContext.user || 'unknown',
        timestamp_utc: new Date().toISOString().slice(0, 19).replace('T', ' ')
      };
    }
  
    private formatLog(message: string, context: LogContext): string {
      return `[${context.timestamp_utc}] - User: ${context.user} - ${context.component || ''} - ${context.action || ''} - ${message}`;
    }
  
    info(message: string, context: Partial<LogContext> = {}): void {
      const fullContext = this.getContext(context);
      console.info(this.formatLog(message, fullContext), context.details || '');
    }
  
    error(message: string, context: Partial<LogContext> = {}): void {
      const fullContext = this.getContext(context);
      console.error(this.formatLog(message, fullContext), context.details || '');
    }
  
    warning(message: string, context: Partial<LogContext> = {}): void {
      const fullContext = this.getContext(context);
      console.warn(this.formatLog(message, fullContext), context.details || '');
    }
  
    success(message: string, context: Partial<LogContext> = {}): void {
      const fullContext = this.getContext(context);
      console.log(this.formatLog(message, fullContext), context.details || '');
    }
  }