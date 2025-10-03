/**
 * WebSocket service for SQL-Guard frontend
 * Handles real-time updates for query execution, approvals, and notifications
 */
import { authService } from './auth';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface QueryUpdateMessage {
  type: 'query_update';
  data: {
    query_id: string;
    status: 'running' | 'completed' | 'failed';
    progress?: number;
    result?: any;
    error?: string;
  };
}

export interface ApprovalUpdateMessage {
  type: 'approval_update';
  data: {
    approval_id: string;
    status: 'pending' | 'approved' | 'rejected';
    template_id: string;
    template_name: string;
    assigned_to: string;
  };
}

export interface SecurityAlertMessage {
  type: 'security_alert';
  data: {
    alert_id: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    user_id: string;
    timestamp: string;
  };
}

export interface NotificationMessage {
  type: 'notification';
  data: {
    id: string;
    title: string;
    message: string;
    type: 'info' | 'warning' | 'error' | 'success';
    timestamp: string;
  };
}

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private isConnecting = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(baseURL: string = WS_BASE_URL) {
    this.url = baseURL;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const wsUrl = `${this.url}/ws?token=${encodeURIComponent(token)}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.reconnectAttempts = 0;
    this.isConnecting = false;
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Send message through WebSocket
   */
  send(message: any): void {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, cannot send message');
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
    }
  }

  /**
   * Subscribe to specific message type
   */
  subscribe(messageType: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }

    this.messageHandlers.get(messageType)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);
    
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Subscribe to query execution updates
   */
  onQueryUpdate(handler: (message: QueryUpdateMessage) => void): () => void {
    return this.subscribe('query_update', handler);
  }

  /**
   * Subscribe to approval updates
   */
  onApprovalUpdate(handler: (message: ApprovalUpdateMessage) => void): () => void {
    return this.subscribe('approval_update', handler);
  }

  /**
   * Subscribe to security alerts
   */
  onSecurityAlert(handler: (message: SecurityAlertMessage) => void): () => void {
    return this.subscribe('security_alert', handler);
  }

  /**
   * Subscribe to notifications
   */
  onNotification(handler: (message: NotificationMessage) => void): () => void {
    return this.subscribe('notification', handler);
  }

  /**
   * Handle WebSocket connection open
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(true));
  }

  /**
   * Handle WebSocket message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle heartbeat response
      if (message.type === 'pong') {
        return;
      }

      // Notify message handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => handler(message));
      }

      // Notify wildcard handlers
      const wildcardHandlers = this.messageHandlers.get('*');
      if (wildcardHandlers) {
        wildcardHandlers.forEach(handler => handler(message));
      }

    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket connection close
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnecting = false;
    
    // Stop heartbeat
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(false));

    // Attempt to reconnect if not manually closed
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.isConnecting = false;
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling WebSocket reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect().catch(error => {
          console.error('Reconnection attempt failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Request to join a specific room/channel
   */
  joinRoom(room: string): void {
    this.send({
      type: 'join_room',
      room: room,
    });
  }

  /**
   * Request to leave a specific room/channel
   */
  leaveRoom(room: string): void {
    this.send({
      type: 'leave_room',
      room: room,
    });
  }

  /**
   * Subscribe to user-specific updates
   */
  subscribeToUser(userId: string): () => void {
    this.joinRoom(`user:${userId}`);
    
    return () => {
      this.leaveRoom(`user:${userId}`);
    };
  }

  /**
   * Subscribe to query-specific updates
   */
  subscribeToQuery(queryId: string): () => void {
    this.joinRoom(`query:${queryId}`);
    
    return () => {
      this.leaveRoom(`query:${queryId}`);
    };
  }

  /**
   * Subscribe to approval-specific updates
   */
  subscribeToApproval(approvalId: string): () => void {
    this.joinRoom(`approval:${approvalId}`);
    
    return () => {
      this.leaveRoom(`approval:${approvalId}`);
    };
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();
export default websocketService;