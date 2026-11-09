# RAKSHAK – Intelligent OS-Based Rescue Scheduling System

## Overview

RAKSHAK is a disaster management platform designed to improve emergency response through intelligent victim prioritization and efficient rescue resource allocation.

This repository contains the Operating System (OS) module developed as part of the RAKSHAK project.

The module focuses on priority-based scheduling, starvation prevention, zone vulnerability analysis, resource allocation, and synchronization.

## Key Features

- **Priority-Based Scheduling:** Calculates victim priority based on emergency severity and vulnerability.
- **Emergency-First Scheduling:** Gives preference to life-threatening rescue cases.
- **Starvation Prevention:** Uses a 600-second waiting threshold to prevent indefinite victim waiting.
- **Zone-Based Prioritization:** Considers disaster-zone risk and vulnerability scores.
- **Resource Management:** Assigns available rescue teams to pending victims.
- **Synchronization:** Uses locking mechanisms to maintain safe dispatch operations.
- **Performance Metrics:** Evaluates scheduling and resource utilization.

## Technology Stack

- Python
- Operating System Concepts
- Object-Oriented Programming
- Thread Synchronization
- Resource Management

## Project Structure

```text
RAKSHAK-OS-Scheduler/
│
├── os_module/
│   ├── __init__.py
│   ├── models.py
│   ├── demo.py
│   ├── metrics.py
│   ├── priority_scheduler.py
│   ├── resource_manager.py
│   ├── scheduler.py
│   ├── synchronization.py
│   └── zone_analyzer.py
│
├── tests/
│   └── test_scheduler.py
│
├── README.md
├── INTEGRATION.md
├── requirements.txt
└── .gitignore
```

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd RAKSHAK-OS-Scheduler
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Execution

Run the OS module demonstration:

```bash
python -m os_module.demo
```

## Testing

Run automated tests:

```bash
python -m pytest tests/ -v
```

## Project Contribution

Developed the Operating System scheduling module for RAKSHAK, implementing intelligent victim prioritization, starvation prevention, zone-based scheduling, synchronization, and rescue resource allocation.

## Integration

The OS scheduling module is designed to work with the RAKSHAK backend. Refer to [INTEGRATION.md](INTEGRATION.md) for integration details.