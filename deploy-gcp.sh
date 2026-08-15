#!/bin/bash
# One-Click Deployment to Google Cloud Run / Google Cloud Platform
set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}
SERVICE_NAME="telegram-job-broadcaster"
REGION="us-central1"

if [ -z "$PROJECT_ID" ]; then
    echo "Please set your GCP_PROJECT_ID or run: gcloud config set project <PROJECT_ID>"
    exit 1
fi

echo "=== Deploying to Google Cloud Run ($SERVICE_NAME) in Project $PROJECT_ID ==="

# Build and submit container image via Google Cloud Build
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Deploy container to Google Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 1 \
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}",TELEGRAM_CHANNEL_ID="@theflashjobupdates",ALERT_CHECK_INTERVAL_MINUTES="2",MAX_JOB_AGE_HOURS="2"

echo "=== Successfully Deployed to Google Cloud Run! Running 24x7. ==="
