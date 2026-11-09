# RAKSHAK OS Module – Backend Integration

## 1. Overview

The RAKSHAK Operating System module is responsible for intelligent rescue scheduling and resource allocation.

It is designed to integrate with the existing RAKSHAK FastAPI backend, which manages victim distress reports, rescue requests, database operations, and dispatch APIs.

## 2. Integration Architecture

```text
RAKSHAK Frontend
       |
       v
FastAPI Backend
       |
       v
Database
       |
       v
Dispatch API
       |
       v
OS Scheduling Module
       |
       +---- Victim Priority Calculation
       |
       +---- Zone Vulnerability Analysis
       |
       +---- Starvation Prevention
       |
       +---- Rescue Team Allocation
       |
       v
Dispatch Result
       |
       v
Backend Response
       |
       v
Frontend
```

## 3. Responsibilities

### Backend Responsibilities

- Receives victim distress reports.
- Stores victim and rescue team information.
- Handles API requests.
- Communicates dispatch information to the frontend.

### OS Module Responsibilities

- Calculates victim priority scores.
- Identifies emergency cases.
- Evaluates zone vulnerability.
- Prevents starvation of waiting victims.
- Allocates available rescue teams.
- Maintains synchronization during dispatch operations.

## 4. Scheduling Mechanisms

### Priority-Based Scheduling
Victims are evaluated using severity, vulnerability, and other scheduling factors.

### Emergency-First Dispatch
Life-threatening cases receive the highest scheduling preference.

### Starvation Prevention
A waiting-time threshold of 600 seconds is used to identify overdue victims.

### Zone-Based Scheduling
Zone risk scores contribute to the selection of victims for rescue.

### Resource Allocation
Available rescue teams are selected according to resource requirements and availability.

### Synchronization
Dispatch operations use locking mechanisms to prevent conflicting resource assignments.

## 5. API Integration

The OS module is connected to the RAKSHAK dispatch workflow through the backend dispatch API.

The backend handles incoming requests and coordinates the scheduling process.

The integration endpoint is:

`POST /api/dispatch/run`

Refer to the actual backend API implementation for request and response schemas.

## 6. Expected Output

The scheduling module provides dispatch information such as:

- Assigned victim ID
- Assigned rescue team ID
- Priority type
- Zone information
- Scheduling result

## 7. Project Contribution

The OS module was developed independently as part of the RAKSHAK disaster management platform, focusing on operating system scheduling concepts and intelligent rescue resource management.