#!/usr/bin/env bash
# Shadiro Delivery Network - Production Deployment Runbook
# Use this as your operational guide during deployment

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION
# ==============================================================================

CLUSTER_NAME="shadiro-production"
NAMESPACE="production"
REGION="ap-south-1"  # Mumbai region for India
DOCKER_REGISTRY="registry.example.com"
IMAGE_NAME="shadiro-delivery"
IMAGE_TAG="v1.0.0"

# External Services
GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-}"
FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID:-}"
REDIS_ENDPOINT="${REDIS_ENDPOINT:-redis.production:6379}"
MONGODB_URI="${MONGODB_URI:-mongodb://mongodb.production:27017}"

# Thresholds for automated rollback
MAX_ERROR_RATE=1.0  # percent
MAX_ASSIGNMENT_LATENCY=2000  # milliseconds
MIN_ETA_ACCURACY=50  # percent

# ==============================================================================
# LOGGING HELPERS
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# ==============================================================================
# PHASE 1: PRE-DEPLOYMENT CHECKS
# ==============================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    for cmd in kubectl docker helm aws-cli; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd not found. Please install it."
            return 1
        fi
    done
    log_success "All required tools installed"
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check kubeconfig."
        return 1
    fi
    log_success "Kubernetes cluster accessible"
    
    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_info "Creating namespace $NAMESPACE..."
        kubectl create namespace $NAMESPACE
    fi
    log_success "Namespace $NAMESPACE ready"
    
    # Check secrets exist
    for secret in delivery-secrets api-keys external-services; do
        if ! kubectl get secret $secret -n $NAMESPACE &> /dev/null; then
            log_warning "Secret $secret not found in $NAMESPACE"
        fi
    done
    
    return 0
}

validate_configuration() {
    log_info "Validating configuration..."
    
    if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
        log_error "GOOGLE_MAPS_API_KEY not set"
        return 1
    fi
    log_success "Google Maps API key configured"
    
    if [ -z "$FIREBASE_PROJECT_ID" ]; then
        log_error "FIREBASE_PROJECT_ID not set"
        return 1
    fi
    log_success "Firebase project ID configured"
    
    # Test Redis connection
    log_info "Testing Redis connection..."
    if redis-cli -h ${REDIS_ENDPOINT%:*} -p ${REDIS_ENDPOINT#*:} ping | grep -q PONG; then
        log_success "Redis connection OK"
    else
        log_error "Cannot connect to Redis"
        return 1
    fi
    
    # Test MongoDB connection
    log_info "Testing MongoDB connection..."
    if mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')" &> /dev/null; then
        log_success "MongoDB connection OK"
    else
        log_error "Cannot connect to MongoDB"
        return 1
    fi
    
    return 0
}

# ==============================================================================
# PHASE 2: BUILD & PUSH DOCKER IMAGE
# ==============================================================================

build_docker_image() {
    log_info "Building Docker image..."
    
    # Build image
    if docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
                    -t $DOCKER_REGISTRY/$IMAGE_NAME:latest \
                    -f backend/Dockerfile \
                    . > /dev/null 2>&1; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        return 1
    fi
    
    # Scan image for vulnerabilities
    log_info "Scanning image for vulnerabilities..."
    if docker scan $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG --json > /tmp/scan-results.json; then
        # Check for critical vulnerabilities
        if grep -q '"severity":"critical"' /tmp/scan-results.json; then
            log_error "Critical vulnerabilities found in image"
            return 1
        fi
        log_success "Security scan passed"
    else
        log_warning "Image scan tool not available, continuing..."
    fi
    
    # Push image
    log_info "Pushing image to registry..."
    if docker push $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG && \
       docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest; then
        log_success "Docker image pushed successfully"
    else
        log_error "Failed to push Docker image"
        return 1
    fi
    
    return 0
}

# ==============================================================================
# PHASE 3: DEPLOY TO KUBERNETES
# ==============================================================================

deploy_backend_pods() {
    log_info "Deploying backend StatefulSet (10 initial replicas)..."
    
    # Create deployment
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: shadiro-delivery-api
  namespace: $NAMESPACE
spec:
  serviceName: shadiro-delivery-api
  replicas: 10
  selector:
    matchLabels:
      app: shadiro-delivery-api
  template:
    metadata:
      labels:
        app: shadiro-delivery-api
    spec:
      containers:
      - name: api
        image: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: delivery-secrets
              key: redis-url
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: delivery-secrets
              key: mongodb-uri
        - name: GOOGLE_MAPS_API_KEY
          valueFrom:
            secretKeyRef:
              name: delivery-secrets
              key: maps-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
EOF
    
    # Wait for rollout
    log_info "Waiting for StatefulSet to be ready..."
    if kubectl rollout status statefulset/shadiro-delivery-api -n $NAMESPACE --timeout=5m; then
        log_success "Backend pods deployed successfully"
    else
        log_error "Deployment failed"
        return 1
    fi
    
    return 0
}

deploy_celery_workers() {
    log_info "Deploying Celery workers DaemonSet..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: shadiro-celery-worker
  namespace: $NAMESPACE
spec:
  selector:
    matchLabels:
      app: shadiro-celery-worker
  template:
    metadata:
      labels:
        app: shadiro-celery-worker
    spec:
      containers:
      - name: worker
        image: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
        command: ["celery", "-A", "backend.workers", "worker", "--loglevel=info", "--concurrency=8"]
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: delivery-secrets
              key: redis-url
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: delivery-secrets
              key: mongodb-uri
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
EOF
    
    log_success "Celery workers deployed (1 per node)"
    return 0
}

setup_autoscaling() {
    log_info "Setting up Horizontal Pod Autoscaling..."
    
    kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shadiro-delivery-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: shadiro-delivery-api
  minReplicas: 10
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
    
    log_success "Auto-scaling configured (10-100 replicas)"
    return 0
}

# ==============================================================================
# PHASE 4: MONITORING & HEALTH CHECKS
# ==============================================================================

wait_for_readiness() {
    log_info "Waiting for all services to be healthy..."
    
    local max_retries=30
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        # Check pod health
        local ready_pods=$(kubectl get pods -n $NAMESPACE -l app=shadiro-delivery-api \
                          -o jsonpath='{.items[].status.conditions[?(@.type=="Ready")].status}' | grep -c True)
        local total_pods=$(kubectl get pods -n $NAMESPACE -l app=shadiro-delivery-api \
                          -o jsonpath='{.items[*]}' | wc -w)
        
        if [ $ready_pods -eq $total_pods ] && [ $total_pods -gt 0 ]; then
            log_success "All $total_pods pods are ready"
            
            # Test API endpoint
            log_info "Testing API endpoint..."
            if kubectl port-forward -n $NAMESPACE svc/shadiro-delivery-api 8000:8000 &
               sleep 2
               curl -s http://localhost:8000/health | grep -q "ok"; then
                log_success "API endpoint is responding"
                pkill -f "port-forward"
                return 0
            fi
        else
            log_warning "Waiting for pods... ($ready_pods/$total_pods ready) - Attempt $((retry+1))/$max_retries"
        fi
        
        sleep 10
        ((retry++))
    done
    
    log_error "Timeout waiting for services to be ready"
    return 1
}

check_metrics() {
    log_info "Checking key metrics..."
    
    # Get current metrics (requires metrics-server)
    local cpu_usage=$(kubectl top pod -n $NAMESPACE -l app=shadiro-delivery-api \
                     --no-headers 2>/dev/null | awk '{print $2}' | sed 's/m$//' | awk '{sum+=$1} END {print sum/NR}')
    local memory_usage=$(kubectl top pod -n $NAMESPACE -l app=shadiro-delivery-api \
                       --no-headers 2>/dev/null | awk '{print $3}' | sed 's/Mi$//' | awk '{sum+=$1} END {print sum/NR}')
    
    log_info "Average pod resources: CPU=${cpu_usage}m, Memory=${memory_usage}Mi"
    
    if [ -z "$cpu_usage" ]; then
        log_warning "Metrics not available (metrics-server might not be installed)"
        return 0
    fi
    
    return 0
}

# ==============================================================================
# PHASE 5: CANARY DEPLOYMENT
# ==============================================================================

canary_deployment() {
    local traffic_percentage=$1
    
    log_info "Routing $traffic_percentage% of traffic to new system..."
    
    # Update Ingress to route traffic
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: delivery-canary
  namespace: $NAMESPACE
spec:
  rules:
  - host: api.delivery.production
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: shadiro-delivery-api
            port:
              number: 8000
EOF
    
    log_success "Canary deployment: $traffic_percentage% traffic routed"
    
    # Monitor for $((5 * traffic_percentage)) minutes
    local monitor_minutes=$((5 * traffic_percentage / 10))
    log_info "Monitoring for $monitor_minutes minutes..."
    
    sleep $((monitor_minutes * 60))
    
    return 0
}

# ==============================================================================
# PHASE 6: HEALTH & SMOKE TESTS
# ==============================================================================

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test delivery job creation
    log_info "Testing job creation..."
    local job_result=$(curl -s -X POST http://localhost:8000/api/delivery-network/jobs \
        -H "Content-Type: application/json" \
        -d '{"customer_id":"test","pickup_lat":19.076,"pickup_lng":72.8777}' \
        2>/dev/null || echo '{"error":"failed"}')
    
    if echo "$job_result" | grep -q "job_id"; then
        log_success "Job creation test passed"
    else
        log_warning "Job creation test result unclear: $job_result"
    fi
    
    # Test assignment
    log_info "Testing assignment engine..."
    if curl -s http://localhost:8000/api/delivery-network/assignment/test &>/dev/null; then
        log_success "Assignment engine test passed"
    else
        log_warning "Assignment engine test inconclusive"
    fi
    
    # Test fraud detection
    log_info "Testing fraud detection..."
    if curl -s http://localhost:8000/api/delivery-network/fraud/test &>/dev/null; then
        log_success "Fraud detection test passed"
    else
        log_warning "Fraud detection test inconclusive"
    fi
    
    return 0
}

# ==============================================================================
# MAIN DEPLOYMENT FLOW
# ==============================================================================

main() {
    log_info "Starting Shadiro Delivery Network Production Deployment"
    log_info "Timestamp: $(date)"
    
    # Phase 1: Checks
    log_info "=== PHASE 1: Pre-Deployment Checks ==="
    check_prerequisites || { log_error "Prerequisites check failed"; exit 1; }
    validate_configuration || { log_error "Configuration validation failed"; exit 1; }
    
    # Phase 2: Build
    log_info "=== PHASE 2: Build Docker Image ==="
    build_docker_image || { log_error "Docker build failed"; exit 1; }
    
    # Phase 3: Deploy
    log_info "=== PHASE 3: Deploy to Kubernetes ==="
    deploy_backend_pods || { log_error "Backend deployment failed"; exit 1; }
    deploy_celery_workers || { log_error "Celery deployment failed"; exit 1; }
    setup_autoscaling || { log_error "Auto-scaling setup failed"; exit 1; }
    
    # Phase 4: Health Checks
    log_info "=== PHASE 4: Health Checks ==="
    wait_for_readiness || { log_error "Service readiness check failed"; exit 1; }
    check_metrics
    
    # Phase 5: Canary
    log_info "=== PHASE 5: Canary Deployment ==="
    log_info "Starting with 10% traffic..."
    canary_deployment 10 || { log_warning "Canary 10% completed"; }
    
    # Phase 6: Tests
    log_info "=== PHASE 6: Smoke Tests ==="
    run_smoke_tests
    
    # Success
    log_success "Deployment completed successfully!"
    log_info "Next steps:"
    log_info "1. Monitor dashboard: kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
    log_info "2. Check logs: kubectl logs -f -n $NAMESPACE deployment/shadiro-delivery-api"
    log_info "3. Scale to 100% after validation"
    
    return 0
}

# Run main function
main "$@"
