# Voting System

A real-time voting system built with FastAPI, MQTT, and Node-RED.

## System Architecture

The following sequence diagram shows how the components interact:

```mermaid
sequenceDiagram
    participant User
    participant Dashboard as Node-RED Dashboard
    participant NodeRED as Node-RED Backend
    participant Broker as MQTT Broker
    participant Server as FastAPI Server
    
    Note over Dashboard,Server: Vote Flow
    User->>Dashboard: Clicks Vote Button
    Dashboard->>NodeRED: Button Event
    NodeRED->>NodeRED: Prepare Vote Message
    NodeRED->>Dashboard: Update Vote Status
    NodeRED->>Broker: Publish to voting/cast
    Broker->>Server: Forward Message
    
    Server->>Server: Process Vote
    Server->>Server: Update Vote Count
    
    Server->>Broker: Publish to voting/results
    Broker->>NodeRED: Forward Results
    NodeRED->>NodeRED: Format Results
    NodeRED->>Dashboard: Update Results Display
    
    Note over Dashboard,Server: Initial Load
    activate Server
    Server->>Broker: Publish Initial Results
    Broker->>NodeRED: Forward Initial Results
    NodeRED->>NodeRED: Format Results
    NodeRED->>Dashboard: Display Initial Results
    deactivate Server
```