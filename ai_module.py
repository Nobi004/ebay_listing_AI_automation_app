import openai
import base64
import json
from typing import List, Dict, Optional
import os
from dataclasses import dataclass

@dataclass
class ProductListing:
    """Data class to hold generated eBay listing details"""
    title: str
    description: str
    category: str
    postage_weight: float
    suggested_price: Optional[float] = None

class eBayListingGenerator:
    """
    Core class for generating eBay listing details using OpenAI API
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the eBay listing generator
        
        Args:
            api_key: OpenAI API key. If None, will try to get from environment variable
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string for OpenAI API
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_product_images(self, image_paths: List[str], user_description: str = "") -> Dict:
        """
        Analyze product images to extract product information
        
        Args:
            image_paths: List of paths to product images
            user_description: Optional user-provided description
            
        Returns:
            Dictionary containing product analysis
        """
        # Prepare images for OpenAI API
        image_contents = []
        for image_path in image_paths[:6]:  # Limit to 6 images
            base64_image = self.encode_image(image_path)
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        # Create the prompt for product analysis
        messages = [
            {
                "role": "system",
                "content": """You are an expert eBay listing assistant. Analyze the provided product images and extract detailed information about the product including:
                - Product type and brand
                - Condition assessment
                - Key features and specifications
                - Materials and dimensions if visible
                - Any defects or wear
                - Estimated value range
                
                Be thorough and accurate in your analysis."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please analyze these product images. Additional user description: {user_description}"
                    }
                ] + image_contents
            }
        ]
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=1000
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def generate_ebay_title(self, product_analysis: str, user_description: str = "") -> str:
        """
        Generate an optimized eBay title
        
        Args:
            product_analysis: Analysis of the product from images
            user_description: Additional user description
            
        Returns:
            Generated eBay title (max 80 characters)
        """
        prompt = f"""
        Based on the product analysis and user description, create an optimized eBay title.
        
        Product Analysis: {product_analysis}
        User Description: {user_description}
        
        Rules for eBay titles:
        - Maximum 80 characters
        - Include brand, model, condition, and key features
        - Use keywords that buyers search for
        - Avoid promotional language like "RARE" or "AMAZING"
        - Include size, color, or other variants if applicable
        
        Generate only the title, no additional text.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert eBay listing title generator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # Ensure title is within eBay's 80 character limit
            return title[:80] if len(title) > 80 else title
            
        except Exception as e:
            return f"Error generating title: {str(e)}"
    
    def generate_ebay_description(self, product_analysis: str, user_description: str = "") -> str:
        """
        Generate a comprehensive eBay description
        
        Args:
            product_analysis: Analysis of the product from images
            user_description: Additional user description
            
        Returns:
            Generated eBay description in HTML format
        """
        prompt = f"""
        Create a comprehensive eBay product description based on the analysis and user input.
        
        Product Analysis: {product_analysis}
        User Description: {user_description}
        
        Structure the description with:
        1. Product overview and key features
        2. Detailed specifications
        3. Condition details
        4. Shipping and return information
        5. Professional closing
        
        Use HTML formatting for better presentation. Include:
        - Bullet points for features
        - Bold text for important information
        - Clear sections and headers
        
        Make it professional and informative to increase buyer confidence.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert eBay listing description writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"<p>Error generating description: {str(e)}</p>"
    
    def categorize_product(self, product_analysis: str, user_description: str = "") -> str:
        """
        Determine the most appropriate eBay category
        
        Args:
            product_analysis: Analysis of the product from images
            user_description: Additional user description
            
        Returns:
            eBay category suggestion
        """
        prompt = f"""
        Based on the product analysis, suggest the most appropriate eBay category.
        
        Product Analysis: {product_analysis}
        User Description: {user_description}
        
        Provide the category in this format: "Main Category > Subcategory > Specific Category"
        
        Common eBay categories include:
        - Electronics > Computers & Tablets > Laptops & Netbooks
        - Fashion > Women's Clothing > Tops & Blouses
        - Home & Garden > Kitchen, Dining & Bar > Small Kitchen Appliances
        - Collectibles > Trading Cards > Sports Trading Cards
        - Books > Fiction & Literature > Contemporary Fiction
        
        Choose the most specific and accurate category possible.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert eBay category classifier."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error categorizing product: {str(e)}"
    
    def estimate_postage_weight(self, product_analysis: str, user_description: str = "") -> float:
        """
        Estimate the postage weight of the product
        
        Args:
            product_analysis: Analysis of the product from images
            user_description: Additional user description
            
        Returns:
            Estimated weight in kg
        """
        prompt = f"""
        Based on the product analysis, estimate the postage weight in kilograms.
        
        Product Analysis: {product_analysis}
        User Description: {user_description}
        
        Consider:
        - Product size and materials
        - Typical weight for similar items
        - Packaging requirements
        - Add 10-15% for packaging materials
        
        Provide only the numeric weight value in kg (e.g., 0.5 for 500g, 2.0 for 2kg).
        Be conservative and slightly overestimate for accurate shipping costs.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert shipping weight estimator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            weight_str = response.choices[0].message.content.strip()
            
            # Extract numeric value from response
            try:
                weight = float(weight_str)
                return max(0.1, weight)  # Minimum 100g for postage
            except ValueError:
                # If conversion fails, return a default weight
                return 0.5
                
        except Exception as e:
            return 0.5  # Default weight if estimation fails
    
    def generate_complete_listing(self, image_paths: List[str], user_description: str = "") -> ProductListing:
        """
        Generate a complete eBay listing with all details
        
        Args:
            image_paths: List of paths to product images
            user_description: Optional user-provided description
            
        Returns:
            ProductListing object with all generated details
        """
        # Step 1: Analyze product images
        analysis_result = self.analyze_product_images(image_paths, user_description)
        
        if not analysis_result["success"]:
            raise Exception(f"Failed to analyze images: {analysis_result['error']}")
        
        product_analysis = analysis_result["analysis"]
        
        # Step 2: Generate all listing components
        title = self.generate_ebay_title(product_analysis, user_description)
        description = self.generate_ebay_description(product_analysis, user_description)
        category = self.categorize_product(product_analysis, user_description)
        weight = self.estimate_postage_weight(product_analysis, user_description)
        
        return ProductListing(
            title=title,
            description=description,
            category=category,
            postage_weight=weight
        )

# Example usage and testing functions
def test_listing_generator():
    """
    Test function to demonstrate the listing generator
    """
    # This would be used for testing with actual images
    generator = eBayListingGenerator()
    
    # Example with dummy image paths
    image_paths = ["product1.jpg", "product2.jpg"]
    user_desc = "Vintage leather jacket, good condition"
    
    try:
        listing = generator.generate_complete_listing(image_paths, user_desc)
        print(f"Title: {listing.title}")
        print(f"Category: {listing.category}")
        print(f"Weight: {listing.postage_weight}kg")
        print(f"Description: {listing.description[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_listing_generator()