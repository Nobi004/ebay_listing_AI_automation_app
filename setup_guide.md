# eBay Listing Generator - Setup Guide

## Overview
This application automatically generates professional eBay listings from product photos using AI. It integrates with OpenAI for content generation, AWS S3 for image storage, and the eBay API for listing creation.

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager

### 2. Required API Keys and Accounts
- OpenAI API key (for AI generation)
- eBay Developer Account (for listing creation)
- AWS Account (for image storage)

## Installation Steps

### 1. Clone or Download the Application
```bash
# Create a new directory for your project
mkdir ebay-listing-generator
cd ebay-listing-generator

# Copy the provided files:
# - ai.py
# - app.py
# - requirements.txt
```

### 2. Install Dependencies
```bash
# Install required Python packages
pip install -r requirements.txt
```

### 3. Set Up API Keys

#### OpenAI API
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or log in
3. Go to API Keys section
4. Generate a new API key
5. Copy the key for environment configuration

#### eBay Developer Account
1. Visit [eBay Developers Program](https://developer.ebay.com/)
2. Create a developer account
3. Create a new application
4. Get your Client ID and Client Secret
5. Configure OAuth redirect URI (e.g., `http://localhost:8501/auth/callback`)

#### AWS S3 Setup
1. Create an AWS account
2. Create an S3 bucket for image storage
3. Create IAM user with S3 permissions
4. Get Access Key ID and Secret Access Key

### 4. Configure Environment Variables

Create a `.env` file in your project directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# eBay API Configuration
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_REDIRECT_URI=http://localhost:8501/auth/callback
EBAY_SANDBOX=true  # Set to false for production

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### 5. Set Environment Variables
```bash
# For Linux/Mac
export OPENAI_API_KEY="your_openai_api_key"
export EBAY_CLIENT_ID="your_ebay_client_id"
export EBAY_CLIENT_SECRET="your_ebay_client_secret"
export EBAY_REDIRECT_URI="http://localhost:8501/auth/callback"
export AWS_ACCESS_KEY_ID="your_aws_access_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
export S3_BUCKET_NAME="your-bucket-name"
export EBAY_SANDBOX="true"

# For Windows
set OPENAI_API_KEY=your_openai_api_key
set EBAY_CLIENT_ID=your_ebay_client_id
# ... (continue with other variables)
```

## Running the Application

### 1. Start the Streamlit App
```bash
streamlit run app.py
```

### 2. Access the Application
Open your browser and go to `http://localhost:8501`

## How to Use

### 1. Upload Product Images
- Click "Browse files" to upload up to 6 product photos
- Use high-quality images with good lighting
- Include multiple angles of the product

### 2. Add Product Description
- Enter any additional details about your product
- Include brand, model, condition, size, color, etc.
- This helps the AI generate more accurate listings

### 3. Generate Listing
- Click "Generate eBay Listing" to analyze images
- The AI will create:
  - Optimized eBay title (max 80 characters)
  - Detailed HTML description
  - Suggested category
  - Estimated shipping weight

### 4. Review and Edit
- Review the generated content in the tabs
- Edit title, description, or weight as needed
- Preview how the listing will look on eBay

### 5. Upload Images to Cloud
- Click "Upload Images to Cloud" to store images in S3
- This provides stable URLs for your eBay listing

### 6. Create eBay Draft
- Click "Create eBay Draft Listing" to submit to eBay
- This creates a draft listing you can review and publish

## Configuration Options

### Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI generation | Yes |
| `EBAY_CLIENT_ID` | eBay API client ID | Yes |
| `EBAY_CLIENT_SECRET` | eBay API client secret | Yes |
| `EBAY_REDIRECT_URI` | OAuth redirect URI | Yes |
| `EBAY_SANDBOX` | Use sandbox (true/false) | No |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `AWS_REGION` | AWS region | No |
| `S3_BUCKET_NAME` | S3 bucket name | Yes |

### AWS S3 Bucket Setup

1. Create a new S3 bucket
2. Configure bucket policy for public read access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

3. Enable CORS for web access:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

## Troubleshooting

### Common Issues

#### 1. Missing API Keys
```
Error: OpenAI API key is required
```
**Solution:** Set the `OPENAI_API_KEY` environment variable

#### 2. Image Upload Errors
```
Error uploading image: NoCredentialsError
```
**Solution:** Configure AWS credentials properly

#### 3. eBay API Errors
```
Error creating listing: Authentication failed
```
**Solution:** Complete eBay OAuth flow or check credentials

#### 4. Memory Issues with Large Images
```
Error: Image too large to process
```
**Solution:** Resize images to under 5MB before uploading

### Performance Tips

1. **Optimize Images:** Use JPEG format, compress to 1-2MB per image
2. **Batch Processing:** Process multiple listings in separate sessions
3. **Monitor API Limits:** Check OpenAI and eBay API usage limits
4. **Use Sandbox:** Test with eBay sandbox before production

## Security Considerations

1. **API Keys:** Never commit API keys to version control
2. **Environment Variables:** Use proper environment variable management
3. **Image Storage:** Ensure S3 bucket has proper access controls
4. **OAuth:** Use HTTPS in production for OAuth callbacks

## Development and Customization

### Extending the AI Module

To customize the AI generation:

1. Modify prompt templates in `ai.py`
2. Add new analysis functions
3. Implement additional product attributes
4. Customize category mapping

### Adding New Storage Providers

To add Google Cloud Storage or other providers:

1. Extend the `CloudStorageManager` class
2. Add provider-specific configuration
3. Implement upload methods for new provider

### Customizing the UI

The Streamlit interface can be customized:

1. Modify layouts in `app.py`
2. Add new configuration options
3. Implement additional preview features
4. Add custom styling with CSS

## License and Usage

This application is designed for educational and commercial use. Ensure compliance with:

- OpenAI API usage policies
- eBay API terms of service
- AWS terms of service
- Local regulations for automated listing creation

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review API documentation for each service
3. Test with minimal examples
4. Check logs for specific error messages

## Next Steps

After setup, consider:

1. Testing with sample products
2. Setting up monitoring for API usage
3. Implementing batch processing for multiple items
4. Adding more sophisticated image analysis
5. Implementing automated pricing suggestions