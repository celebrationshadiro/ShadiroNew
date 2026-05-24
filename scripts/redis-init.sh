#!/bin/sh
set -e

echo "Waiting for all Redis nodes to be online..."
for host in redis-node-1 redis-node-2 redis-node-3 redis-node-4 redis-node-5 redis-node-6; do
  until redis-cli -h "$host" -p 6379 ping | grep -q "PONG"; do
    echo "Waiting for $host:6379..."
    sleep 2
  done
done

echo "All Redis nodes are active. Launching cluster configuration..."

echo "yes" | redis-cli --cluster create \
  redis-node-1:6379 \
  redis-node-2:6379 \
  redis-node-3:6379 \
  redis-node-4:6379 \
  redis-node-5:6379 \
  redis-node-6:6379 \
  --cluster-replicas 1

echo "Redis Cluster configured and operational!"
