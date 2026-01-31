# Event Bus Module
# Real-time updates event bus

class EventBus:
    """Event bus for real-time updates"""
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_type, callback):
        """Subscribe to an event type"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def publish(self, event_type, data):
        """Publish an event"""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(data)

# Global event bus instance
event_bus = EventBus()
