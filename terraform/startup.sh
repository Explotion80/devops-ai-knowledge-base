#!/bin/bash
set -e

# Install Docker
apt-get update
apt-get install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Clone repo
if [ ! -d /opt/ai-kb/.git ]; then
  git clone https://github.com/Explotion80/devops-ai-knowledge-base.git /opt/ai-kb
else
  cd /opt/ai-kb && git pull origin main
fi

# Create .env
cat > /opt/ai-kb/.env <<EOF
OPENAI_API_KEY=${openai_api_key}
EOF
chmod 600 /opt/ai-kb/.env

# Start app
cd /opt/ai-kb
docker compose -f docker-compose.prod.yml up -d --build
