# FairPayEngine Web Application Deployment Guide

## Quick Start
1. Build Docker image:
```bash
docker build --rm -t webapp-fair-pay-engine .
```

2. Run container:
```bash
docker run -d -p 5002:5002 webapp-fair-pay-engine:latest
```

3. Access application:
```
http://localhost:5002
```

## References
- [reddit](https://www.reddit.com/r/flask/comments/vhcpqa/best_way_to_deploy_a_flask_app_internally_and/)
- [levelup blog](https://levelup.gitconnected.com/dockerizing-a-flask-application-with-a-postgres-database-b5e5bfc24848)
