# Service Specification — Lab 4

Author: Abdrakhmanova Adel
Version: 3

## 1. Purpose

The purpose of this service is to demonstrate a stateless REST API
implemented in Python using Flask.

In Laboratory Work 3 the service is containerized using Docker
and deployed in multiple replicas using Kubernetes.

## 2. Endpoints

| ID | Method | Path                          | Input                 | Output                                    | Response Codes |
|----|--------|-------------------------------|-----------------------|-------------------------------------------|----------------|
| R1 | POST   | /echo                         | {"message": "string"} | {"reply": "string"}                       | 200, 400       |
| R2 | GET    | /time                         | none                  | {"time": "string", "served_by": "string"} | 200            |
| R5 | POST   | /files                        | {"text":"string"}     | {"file_id":"UUID"}                        | 201, 400, 503  |
| R6 | GET    | /files/<file_id>              | file ID               | file text                                 | 200, 404, 503  |
| R7 | POST   | /counter/increment            | none                  | counter value                             | 200, 503       |
| R8 | GET    | /counter?from=primary/replica | source                | counter value                             | 200, 400, 503  |

## 3. Constraints

- The service uses HTTP.
- JSON is used for data exchange.
- Python 3 and Flask are used.
- The application listens on port 5000.
- The application listens on 0.0.0.0 inside the container.
- Docker is used for containerization.
- Kubernetes is used for deployment and scaling.
- The application is stateless.
- Queue processing from Laboratory Work 2 is outside the scope of Lab 4
- Maximum file size: 10 KB

## 4. Non-functional Requirements

- N1: /echo should respond within 200 ms under normal local execution.
- N2: /time should respond within 200 ms under normal local execution.
- N3: Kubernetes must maintain 3 running replicas during normal operation.
- N4: after deleting one pod, Kubernetes must automatically create a replacement.
- N5: the deployment must be scalable from 3 to 5 replicas.

## 5. Assumptions

- A1: Docker Desktop is installed and running.
- A2: minikube and kubectl are installed.
- A3: at least 8 GB of RAM is available.
- A4: all replicas run the same Docker image.
- A5: a read from a Redis replica may return a stale value because replication is asynchronous.