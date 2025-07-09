import streamlit as st
import os
import json
import tempfile
from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError
import requests
from PIL import Image
import io
import base64
from datetime import datetime, timedelta

# Import our AI module
from ai import eBayListingGenerator, ProductListing

class CloudStorageManager:
    """
    Manages cloud storage operations for product images
    """
    
    def __init__(self, storage_type: str = "s3"):
        self.storage_type = storage_type
        
        if storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    def upload_image(self, image_file, filename: str) -> str:
        """
        Upload image to cloud storage
        
        Args:
            image_file: File object or bytes
            filename: Name for the file in storage
            
        Returns:
            URL of the uploaded image
        """
        try:
            if self.storage_type == "s3":
                self.s3_client.upload_fileobj(
                    image_file, 
                    self.bucket_name, 
                    filename,
                    ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'}
                )
                return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
            
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")
            return None
    
    def upload_multiple_images(self, image_files: List) -> List[str]:
        """
        Upload multiple images to cloud storage
        
        Args:
            image_files: List of image file objects
            
        Returns:
            List of URLs of uploaded images
        """
        urls = []
        for i, image_file in enumerate(image_files):
            if image_file is not None:
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"product_images/{timestamp}_{i}.jpg"
                
                # Reset file pointer
                image_file.seek(0)
                
                url = self.upload_image(image_file, filename)
                if url:
                    urls.append(url)
        
        return urls

class eBayAPIManager:
    """
    Manages eBay API interactions for creating listings
    """
    
    def __init__(self):
        self.client_id = os.getenv('EBAY_CLIENT_ID')
        self.client_secret = os.getenv('EBAY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('EBAY_REDIRECT_URI')
        self.access_token = None
        self.refresh_token = None
        
        # eBay API endpoints
        self.sandbox_base_url = "https://api.sandbox.ebay.com"
        self.production_base_url = "https://api.ebay.com"
        self.is_sandbox = os.getenv('EBAY_SANDBOX', 'true').lower() == 'true'
        self.base_url = self.sandbox_base_url if self.is_sandbox else self.production_base_url
    
    def get_oauth_url(self) -> str:
        """
        Get OAuth authorization URL for eBay
        
        Returns:
            OAuth URL for user authorization
        """
        scope = "https://api.ebay.com/oauth/api_scope/sell.inventory"
        oauth_url = f"https://auth.ebay.com/oauth2/authorize?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}&scope={scope}"
        return oauth_url
    
    def get_access_token(self, authorization_code: str) -> bool:
        """
        Exchange authorization code for access token
        
        Args:
            authorization_code: Code from eBay OAuth callback
            
        Returns:
            True if successful, False otherwise
        """
        token_url = f"{self.base_url}/identity/v1/oauth2/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            return True
            
        except requests.RequestException as e:
            st.error(f"Error getting access token: {str(e)}")
            return False
    
    def create_draft_listing(self, listing: ProductListing, image_urls: List[str]) -> Dict:
        """
        Create a draft listing on eBay
        
        Args:
            listing: ProductListing object with generated details
            image_urls: List of URLs for product images
            
        Returns:
            Dictionary with listing creation result
        """
        if not self.access_token:
            return {"success": False, "error": "No access token available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        # Prepare listing data
        listing_data = {
            "product": {
                "title": listing.title,
                "description": listing.description,
                "imageUrls": image_urls,
                "aspects": {
                    "Brand": ["Generic"],  # This would be extracted from analysis
                    "Condition": ["Used"]  # This would be determined from analysis
                }
            },
            "condition": "USED_EXCELLENT",
            "format": "FIXED_PRICE",
            "marketplaceId": "EBAY_US",
            "categoryId": "1234",  # This would be mapped from our category
            "listingPolicies": {
                "fulfillmentPolicyId": "policy_id",
                "paymentPolicyId": "policy_id",
                "returnPolicyId": "policy_id"
            },
            "pricingSummary": {
                "price": {
                    "currency": "USD",
                    "value": "10.00"  # This would be suggested by AI
                }
            },
            "merchantLocationKey": "warehouse_location",
            "tax": {
                "applyTax": True,
                "vatPercentage": 0.0
            }
        }
        
        try:
            url = f"{self.base_url}/sell/inventory/v1/inventory_item/draft"
            response = requests.post(url, headers=headers, json=listing_data)
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "listing_id": response.json().get("sku"),
                    "message": "Draft listing created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def init_session_state():
    """
    Initialize Streamlit session state variables
    """
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []
    if 'generated_listing' not in st.session_state:
        st.session_state.generated_listing = None
    if 'image_urls' not in st.session_state:
        st.session_state.image_urls = []
    if 'listing_created' not in st.session_state:
        st.session_state.listing_created = False

def display_image_upload():
    """
    Display the image upload interface
    """
    st.subheader("📸 Upload Product Images")
    st.write("Upload up to 6 high-quality photos of your product. Good lighting and multiple angles help generate better listings.")
    
    # File uploader for multiple images
    uploaded_files = st.file_uploader(
        "Choose product images",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Upload up to 6 images. First image will be the main listing photo."
    )
    
    if uploaded_files:
        # Limit to 6 images
        if len(uploaded_files) > 6:
            st.warning("Only the first 6 images will be used.")
            uploaded_files = uploaded_files[:6]
        
        # Display preview of uploaded images
        st.write(f"**{len(uploaded_files)} image(s) uploaded:**")
        
        cols = st.columns(3)
        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 3]:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Image {i+1}", use_column_width=True)
        
        st.session_state.uploaded_images = uploaded_files
        return True
    
    return False

def display_description_input():
    """
    Display the description input interface
    """
    st.subheader("📝 Product Description")
    
    user_description = st.text_area(
        "Add any additional details about your product",
        placeholder="e.g., Brand, model, condition, size, color, any defects, purchase date, etc.",
        height=120,
        help="Provide any additional context that might not be visible in the photos. This helps generate more accurate listings."
    )
    
    return user_description

def display_generated_listing(listing: ProductListing):
    """
    Display the generated listing details
    """
    st.subheader("🎯 Generated eBay Listing")
    
    # Display in tabs for better organization
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Title & Category", "📖 Description", "📦 Shipping", "🎨 Preview"])
    
    with tab1:
        st.write("**eBay Title:**")
        title_col1, title_col2 = st.columns([3, 1])
        with title_col1:
            edited_title = st.text_input("Edit title if needed:", value=listing.title)
        with title_col2:
            st.metric("Characters", len(edited_title), delta=f"{len(edited_title)-80} over limit" if len(edited_title) > 80 else "✓")
        
        st.write("**Suggested Category:**")
        st.info(listing.category)
    
    with tab2:
        st.write("**Generated Description:**")
        edited_description = st.text_area(
            "Edit description if needed:",
            value=listing.description,
            height=300
        )
        
        # Preview the HTML
        if edited_description:
            st.write("**Preview:**")
            st.markdown(edited_description, unsafe_allow_html=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Weight", f"{listing.postage_weight} kg")
        with col2:
            # Allow user to override weight
            override_weight = st.number_input(
                "Override weight (kg):",
                min_value=0.1,
                max_value=30.0,
                value=listing.postage_weight,
                step=0.1
            )
    
    with tab4:
        st.write("**How your listing will look:**")
        
        # Mock eBay listing preview
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; background: white;">
            <h3 style="color: #0053A1; margin-top: 0;">{edited_title}</h3>
            <div style="margin: 10px 0;">
                <span style="background: #E5F3FF; padding: 2px 8px; border-radius: 3px; font-size: 12px;">
                    {listing.category}
                </span>
            </div>
            <div style="margin: 10px 0; font-size: 14px;">
                <strong>Weight:</strong> {listing.postage_weight} kg
            </div>
            <div style="margin-top: 15px;">
                {edited_description}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Update the listing with edits
    listing.title = edited_title
    listing.description = edited_description
    listing.postage_weight = override_weight
    
    return listing

def main():
    """
    Main Streamlit application
    """
    st.set_page_config(
        page_title="eBay Listing Generator",
        page_icon="🏷️",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🏷️ eBay Listing Generator")
    st.markdown("*Automatically generate professional eBay listings from product photos using AI*")
    
    # Sidebar with configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check if required environment variables are set
        required_vars = ['OPENAI_API_KEY', 'EBAY_CLIENT_ID', 'AWS_ACCESS_KEY_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            st.error(f"Missing environment variables: {', '.join(missing_vars)}")
            st.stop()
        else:
            st.success("✅ All API keys configured")
        
        # Runtime options
        st.subheader("Options")
        use_sandbox = st.checkbox("Use eBay Sandbox", value=True, help="Use eBay sandbox for testing")
        auto_upload_images = st.checkbox("Auto-upload images to cloud", value=True, help="Automatically upload images to cloud storage")
        
        # Information
        st.subheader("ℹ️ How it works")
        st.write("""
        1. Upload up to 6 product photos
        2. Add optional description
        3. AI analyzes images and generates listing
        4. Review and edit the generated content
        5. Create draft listing on eBay
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Step 1: Image Upload
        has_images = display_image_upload()
        
        # Step 2: Description Input
        user_description = display_description_input()
        
        # Step 3: Generate Listing
        if has_images and st.button("🚀 Generate eBay Listing", type="primary"):
            with st.spinner("Analyzing images and generating listing..."):
                try:
                    # Initialize the AI generator
                    generator = eBayListingGenerator()
                    
                    # Save uploaded images to temporary files
                    temp_paths = []
                    for i, uploaded_file in enumerate(st.session_state.uploaded_images):
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_paths.append(tmp_file.name)
                    
                    # Generate the listing
                    listing = generator.generate_complete_listing(temp_paths, user_description)
                    st.session_state.generated_listing = listing
                    
                    # Clean up temporary files
                    for path in temp_paths:
                        try:
                            os.unlink(path)
                        except:
                            pass
                    
                    st.success("✅ Listing generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating listing: {str(e)}")
    
    with col2:
        # Display generated listing if available
        if st.session_state.generated_listing:
            final_listing = display_generated_listing(st.session_state.generated_listing)
            
            # Upload images to cloud storage if enabled
            if auto_upload_images and st.button("☁️ Upload Images to Cloud"):
                with st.spinner("Uploading images to cloud storage..."):
                    try:
                        storage_manager = CloudStorageManager()
                        
                        # Convert uploaded files to file objects
                        image_files = []
                        for uploaded_file in st.session_state.uploaded_images:
                            uploaded_file.seek(0)
                            image_files.append(uploaded_file)
                        
                        image_urls = storage_manager.upload_multiple_images(image_files)
                        st.session_state.image_urls = image_urls
                        
                        st.success(f"✅ {len(image_urls)} images uploaded successfully!")
                        
                        # Display uploaded image URLs
                        with st.expander("View uploaded image URLs"):
                            for i, url in enumerate(image_urls):
                                st.write(f"Image {i+1}: {url}")
                    
                    except Exception as e:
                        st.error(f"Error uploading images: {str(e)}")
            
            # Create eBay draft listing
            if st.session_state.image_urls and st.button("📝 Create eBay Draft Listing"):
                with st.spinner("Creating draft listing on eBay..."):
                    try:
                        ebay_manager = eBayAPIManager()
                        
                        # For demonstration, we'll show what would be sent to eBay
                        if not ebay_manager.access_token:
                            st.warning("eBay authentication required. This would normally redirect to eBay for authorization.")
                            st.info("Draft listing would be created with the following details:")
                            
                            listing_preview = {
                                "title": final_listing.title,
                                "description": final_listing.description[:200] + "...",
                                "category": final_listing.category,
                                "weight": final_listing.postage_weight,
                                "image_count": len(st.session_state.image_urls),
                                "image_urls": st.session_state.image_urls
                            }
                            
                            st.json(listing_preview)
                        else:
                            result = ebay_manager.create_draft_listing(final_listing, st.session_state.image_urls)
                            
                            if result["success"]:
                                st.success(f"✅ Draft listing created! ID: {result['listing_id']}")
                                st.session_state.listing_created = True
                            else:
                                st.error(f"❌ Error creating listing: {result['error']}")
                    
                    except Exception as e:
                        st.error(f"Error creating eBay listing: {str(e)}")
    
    # Footer with additional options
    if st.session_state.listing_created:
        st.success("🎉 Your eBay listing has been created as a draft! You can now visit eBay to review and publish it.")
        
        if st.button("🔄 Create Another Listing"):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

# Configuration check function
def check_configuration():
    """
    Check if all required environment variables are set
    """
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for AI generation',
        'EBAY_CLIENT_ID': 'eBay API client ID',
        'EBAY_CLIENT_SECRET': 'eBay API client secret',
        'EBAY_REDIRECT_URI': 'eBay OAuth redirect URI',
        'AWS_ACCESS_KEY_ID': 'AWS access key for S3 storage',
        'AWS_SECRET_ACCESS_KEY': 'AWS secret key for S3 storage',
        'S3_BUCKET_NAME': 'S3 bucket name for image storage'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        st.error("Missing required environment variables:")
        for var in missing:
            st.write(f"- {var}")
        
        st.info("""
        Please set the following environment variables:
        
        ```bash
        export OPENAI_API_KEY="your_openai_api_key"
        export EBAY_CLIENT_ID="your_ebay_client_id"
        export EBAY_CLIENT_SECRET="your_ebay_client_secret"
        export EBAY_REDIRECT_URI="your_redirect_uri"
        export AWS_ACCESS_KEY_ID="your_aws_access_key"
        export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
        export S3_BUCKET_NAME="your_s3_bucket_name"
        export EBAY_SANDBOX="true"  # Use false for production
        ```
        """)
        
        return False
    
    return True

if __name__ == "__main__":
    if check_configuration():
        main()
    else:
        st.stop()