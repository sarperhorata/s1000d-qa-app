#!/bin/bash
# Azure Deployment Script for S1000D QA Application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== S1000D QA Application - Azure Deployment ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Load environment variables from .env.azure
if [ -f .env.azure ]; then
    export $(cat .env.azure | grep -v '^#' | xargs)
else
    echo -e "${RED}.env.azure file not found!${NC}"
    exit 1
fi

# Validate required variables
if [ -z "$AZURE_RESOURCE_GROUP" ] || [ -z "$AZURE_CONTAINER_REGISTRY" ] || [ -z "$AZURE_CONTAINER_APP_NAME" ]; then
    echo -e "${RED}Required environment variables not set in .env.azure${NC}"
    echo "Please set: AZURE_RESOURCE_GROUP, AZURE_CONTAINER_REGISTRY, AZURE_CONTAINER_APP_NAME"
    exit 1
fi

# Login to Azure (if not already logged in)
echo -e "${YELLOW}Checking Azure login status...${NC}"
az account show &> /dev/null || az login

# Set default subscription (optional)
# az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Variables
LOCATION=${AZURE_LOCATION:-"eastus"}
IMAGE_NAME="s1000d-qa-app"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${AZURE_CONTAINER_REGISTRY}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${GREEN}Configuration:${NC}"
echo "  Resource Group: $AZURE_RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Container Registry: $AZURE_CONTAINER_REGISTRY"
echo "  Container App: $AZURE_CONTAINER_APP_NAME"
echo "  Image: $FULL_IMAGE_NAME"
echo ""

# Step 1: Create Resource Group (if it doesn't exist)
echo -e "${YELLOW}Step 1: Creating/Verifying Resource Group...${NC}"
az group create --name $AZURE_RESOURCE_GROUP --location $LOCATION

# Step 2: Create Container Registry (if it doesn't exist)
echo -e "${YELLOW}Step 2: Creating/Verifying Container Registry...${NC}"
az acr show --name $AZURE_CONTAINER_REGISTRY --resource-group $AZURE_RESOURCE_GROUP &> /dev/null || \
    az acr create \
        --resource-group $AZURE_RESOURCE_GROUP \
        --name $AZURE_CONTAINER_REGISTRY \
        --sku Basic \
        --admin-enabled true

# Step 3: Build and Push Docker Image
echo -e "${YELLOW}Step 3: Building Docker Image...${NC}"
docker build -f Dockerfile.azure -t $IMAGE_NAME:$IMAGE_TAG .

echo -e "${YELLOW}Step 4: Logging in to Azure Container Registry...${NC}"
az acr login --name $AZURE_CONTAINER_REGISTRY

echo -e "${YELLOW}Step 5: Tagging and Pushing Image...${NC}"
docker tag $IMAGE_NAME:$IMAGE_TAG $FULL_IMAGE_NAME
docker push $FULL_IMAGE_NAME

# Step 4: Create Container Apps Environment (if it doesn't exist)
ENVIRONMENT_NAME="${AZURE_CONTAINER_APP_NAME}-env"
echo -e "${YELLOW}Step 6: Creating/Verifying Container Apps Environment...${NC}"
az containerapp env show --name $ENVIRONMENT_NAME --resource-group $AZURE_RESOURCE_GROUP &> /dev/null || \
    az containerapp env create \
        --name $ENVIRONMENT_NAME \
        --resource-group $AZURE_RESOURCE_GROUP \
        --location $LOCATION

# Step 5: Create/Update Container App
echo -e "${YELLOW}Step 7: Deploying Container App...${NC}"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $AZURE_CONTAINER_REGISTRY --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $AZURE_CONTAINER_REGISTRY --query passwords[0].value -o tsv)

# Check if app exists
az containerapp show --name $AZURE_CONTAINER_APP_NAME --resource-group $AZURE_RESOURCE_GROUP &> /dev/null

if [ $? -eq 0 ]; then
    # Update existing app
    echo -e "${YELLOW}Updating existing Container App...${NC}"
    az containerapp update \
        --name $AZURE_CONTAINER_APP_NAME \
        --resource-group $AZURE_RESOURCE_GROUP \
        --image $FULL_IMAGE_NAME
else
    # Create new app
    echo -e "${YELLOW}Creating new Container App...${NC}"
    az containerapp create \
        --name $AZURE_CONTAINER_APP_NAME \
        --resource-group $AZURE_RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $FULL_IMAGE_NAME \
        --target-port 8000 \
        --ingress external \
        --registry-server "${AZURE_CONTAINER_REGISTRY}.azurecr.io" \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --cpu 1.0 \
        --memory 2.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            ENVIRONMENT=azure \
            VECTOR_STORE_TYPE=chromadb \
            CHROMA_PERSIST_DIR=/app/chroma_data \
            OCR_ENABLED=true \
            OCR_ENGINE=tesseract
fi

# Step 6: Get App URL
echo -e "${YELLOW}Step 8: Getting Application URL...${NC}"
APP_URL=$(az containerapp show \
    --name $AZURE_CONTAINER_APP_NAME \
    --resource-group $AZURE_RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Application URL: https://$APP_URL${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Upload S1000D PDF to Azure Blob Storage"
echo "2. Configure environment variables in Azure Portal"
echo "3. Set up Azure Key Vault for secrets"
echo "4. Configure custom domain (optional)"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs: az containerapp logs show --name $AZURE_CONTAINER_APP_NAME --resource-group $AZURE_RESOURCE_GROUP --follow"
echo "  View app: az containerapp show --name $AZURE_CONTAINER_APP_NAME --resource-group $AZURE_RESOURCE_GROUP"
echo "  Delete app: az containerapp delete --name $AZURE_CONTAINER_APP_NAME --resource-group $AZURE_RESOURCE_GROUP"

