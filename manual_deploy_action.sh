#!/bin/bash

# Define server details
SERVER_USER="hafar"
SERVER_IP="64.23.169.164"
DEPLOY_SCRIPT="/home/hafar/hafar_backend/deploy.sh"

echo "🚀 Auto-deploying after push..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "bash $DEPLOY_SCRIPT"
echo "✅ Deployment complete!"
