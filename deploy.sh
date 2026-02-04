#!/bin/bash
# Deployment script for AWS Lambda using uv
set -e

echo "Building Lambda deployment package..."

# Clean up previous builds
rm -rf lambda_package lambda_function.zip

# Create package directory
mkdir -p lambda_package

# Install dependencies to the package directory
echo "Installing dependencies with uv..."
uv pip install --python 3.12 --target lambda_package \
    feedparser>=6.0.11 \
    boto3>=1.35.86 \
    requests>=2.32.3

# Copy source code
echo "Copying source code..."
cp -r src/* lambda_package/

# Create ZIP file
echo "Creating deployment package..."
cd lambda_package
zip -r ../lambda_function.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

echo "Deployment package created: lambda_function.zip"
echo "Package size: $(du -h lambda_function.zip | cut -f1)"
echo ""
echo "To deploy to AWS Lambda, run:"
echo "  aws lambda update-function-code --function-name aws-jp-blog-feed-notifier --zip-file fileb://lambda_function.zip"
