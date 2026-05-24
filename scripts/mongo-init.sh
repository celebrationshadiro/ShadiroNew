#!/bin/sh
set -e

echo "Waiting for mongodb-node-1 to accept connections..."
until mongo --host mongodb-node-1:27017 --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
  sleep 2
done

echo "Initializing MongoDB replica set rs0..."
mongo --host mongodb-node-1:27017 --eval "
  rs.initiate({
    _id: 'rs0',
    members: [
      { _id: 0, host: 'mongodb-node-1:27017', priority: 2 },
      { _id: 1, host: 'mongodb-node-2:27017', priority: 1 },
      { _id: 2, host: 'mongodb-node-3:27017', priority: 1 }
    ]
  })
"

echo "Replica set rs0 initialized successfully!"
