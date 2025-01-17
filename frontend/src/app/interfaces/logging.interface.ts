export interface LogContext {
    timestamp_utc: string;
    user: string;
    component?: string;
    action?: string;
    details?: any;
  }
  