import streamlit as st
import pandas as pd
import io
import os
from PIL import Image
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, that's okay

# Title
st.title("📸 Receipt → CSV")
st.markdown("*Parse receipts with Azure AI*")

# Add mobile-friendly styling
st.markdown("""
<style>
    /* Mobile-friendly adjustments */
    .stFileUploader label {
        font-size: 16px !important;
        padding: 10px !important;
    }
    
    .stDataFrame {
        font-size: 14px;
    }
    
    /* Make buttons more touch-friendly */
    .stDownloadButton button {
        padding: 10px 20px !important;
        font-size: 16px !important;
    }
    
    /* Improve spacing on mobile */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Check for required environment variables
AZURE_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT") or st.secrets.get("azure_endpoint", "")
AZURE_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY") or st.secrets.get("azure_key", "")

if not AZURE_ENDPOINT or not AZURE_KEY:
    st.error("""
    ⚠️ **Missing Azure credentials!** 
    
    Please set the following environment variables:
    - `AZURE_FORM_RECOGNIZER_ENDPOINT`: Your Azure Form Recognizer endpoint URL
    - `AZURE_FORM_RECOGNIZER_KEY`: Your Azure Form Recognizer key
    
    You can set them in your terminal:
    ```bash
    export AZURE_FORM_RECOGNIZER_ENDPOINT="your_endpoint_here"
    export AZURE_FORM_RECOGNIZER_KEY="your_key_here"
    ```
    
    Or create a `.env` file in this directory with:
    ```
    AZURE_FORM_RECOGNIZER_ENDPOINT=your_endpoint_here
    AZURE_FORM_RECOGNIZER_KEY=your_key_here
    ```
    """)
    st.stop()

# 1. Upload CSV template
st.subheader("1️⃣ Upload Template")
tpl = st.file_uploader("Upload CSV template", type="csv", help="Upload your CSV template to define the output structure")
if not tpl:
    st.info("👆 Please upload a CSV template to get started")
    st.stop()
df_tpl = pd.read_csv(tpl)
st.success(f"✅ Template loaded with {len(df_tpl.columns)} columns")

# 2. Capture or upload receipt image
st.subheader("2️⃣ Add Receipt")
col1, col2 = st.columns([1, 1])

with col1:
    img_camera = st.camera_input("📸 Take Photo")
    
with col2:
    img_upload = st.file_uploader("📁 Upload Image", type=["jpg","png","jpeg"])

img = img_camera or img_upload
if not img:
    st.info("📱 Take a photo or upload a receipt image to continue")
    st.stop()

# Display the uploaded/captured image
st.image(img, caption="📸 Receipt Image", use_column_width=True)

# 3. Read image bytes
if hasattr(img, "read"):
    img_bytes = img.read()
else:
    buf = io.BytesIO()
    Image.open(img).save(buf, format="JPEG")
    img_bytes = buf.getvalue()

# 4. Analyze with Azure Form Recognizer
client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)
poller = client.begin_analyze_document("prebuilt-receipt", img_bytes)
res = poller.result()
rcpt = res.documents[0]
fields = rcpt.fields

# 5. Extract summary information
# Try different field names for merchant
merchant_name = ""
for merchant_field in ["MerchantName", "Merchant", "VendorName", "CompanyName"]:
    if merchant_field in fields and fields[merchant_field].value:
        merchant_name = fields[merchant_field].value
        break

# If no merchant found in standard fields, try to extract from other places
if not merchant_name:
    # Check if there's a MerchantAddress field that might contain merchant info
    if "MerchantAddress" in fields and fields["MerchantAddress"].value:
        # Sometimes the first line of the address contains the merchant name
        address_lines = str(fields["MerchantAddress"].value).split('\n')
        if address_lines:
            merchant_name = address_lines[0].strip()
    
    # Try to extract from raw text content (last resort)
    elif hasattr(res, 'content') and res.content:
        # This extracts all text and tries to find a business name pattern
        # Look for the first line that's not a number, date, or address
        lines = res.content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Skip empty lines, numbers, dates, addresses
            if (line and 
                not line.replace('.', '').replace('-', '').replace('/', '').isdigit() and
                not any(word in line.lower() for word in ['phone', 'tel', 'address', 'street', 'ave', 'rd', 'blvd']) and
                len(line) > 2):
                merchant_name = line
                break
    
    # Final fallback
    if not merchant_name:
        merchant_name = "Unknown Merchant"

# Try different field names for date
transaction_date = ""
for date_field in ["TransactionDate", "Date", "PurchaseDate", "InvoiceDate"]:
    if date_field in fields and fields[date_field].value:
        transaction_date = fields[date_field].value
        break

# Try different field names for total
total_amount = ""
for total_field in ["Total", "InvoiceTotal", "TotalAmount", "GrandTotal"]:
    if total_field in fields and fields[total_field].value:
        total_amount = fields[total_field].value
        break

# 6. Extract line items and create rows matching template
rows = []
if "Items" in fields and fields["Items"].value:
    # Process each item from the receipt
    for item in fields["Items"].value:
        row = {}
        
        # Start with template columns (ensures all columns exist)
        for col in df_tpl.columns:
            row[col] = ""
        
        # Fill in the extracted data
        row["Date"] = transaction_date
        row["Merchant"] = merchant_name
        
        # Extract item details
        item_data = item.value
        
        # Get item name/description
        item_name = ""
        if "Name" in item_data:
            item_name = item_data["Name"].value
        elif "Description" in item_data:
            item_name = item_data["Description"].value
        
        # Get quantity (if available)
        quantity = 1  # Default to 1
        if "Quantity" in item_data and item_data["Quantity"].value:
            try:
                quantity = float(item_data["Quantity"].value)
            except (ValueError, TypeError):
                quantity = 1
        
        # Get unit price and total price
        unit_price = None
        total_price = None
        
        if "TotalPrice" in item_data and item_data["TotalPrice"].value:
            total_price = item_data["TotalPrice"].value
        elif "Price" in item_data and item_data["Price"].value:
            total_price = item_data["Price"].value
            
        if "UnitPrice" in item_data and item_data["UnitPrice"].value:
            unit_price = item_data["UnitPrice"].value
        
        # Calculate missing values if possible
        if unit_price and not total_price:
            total_price = unit_price * quantity
        elif total_price and not unit_price and quantity > 0:
            unit_price = total_price / quantity
        
        # If quantity > 1, show it in the item name
        if quantity > 1:
            row["Item"] = f"{quantity}x {item_name}" if item_name else f"{quantity}x Item"
        else:
            row["Item"] = item_name
            
        # Use total price for the Price field
        row["Price"] = total_price if total_price else unit_price
        
        # If template has a "Unit Price" column, populate it
        if "Unit Price" in df_tpl.columns:
            row["Unit Price"] = unit_price
        
        # If template has a "Quantity" column, populate it
        if "Quantity" in df_tpl.columns:
            row["Quantity"] = quantity
        
        # If we have a unit price and quantity > 1, add unit price info to item description
        if quantity > 1 and unit_price and unit_price != total_price:
            try:
                unit_price_float = float(unit_price)
                row["Item"] = f"{quantity}x {item_name} (@${unit_price_float:.2f} each)" if item_name else f"{quantity}x Item (@${unit_price_float:.2f} each)"
            except (ValueError, TypeError):
                # If unit_price can't be converted to float, just show the basic format
                row["Item"] = f"{quantity}x {item_name} (@{unit_price} each)" if item_name else f"{quantity}x Item (@{unit_price} each)"
            
        rows.append(row)
    
    # Add tax as a separate line item if present
    if "TotalTax" in fields and fields["TotalTax"].value:
        tax_row = {}
        for col in df_tpl.columns:
            tax_row[col] = ""
        
        tax_row["Date"] = transaction_date
        tax_row["Merchant"] = merchant_name
        tax_row["Item"] = "Tax"
        tax_row["Price"] = fields["TotalTax"].value
        rows.append(tax_row)
        
    # Add total row
    total_row = {}
    for col in df_tpl.columns:
        total_row[col] = ""
    
    total_row["Date"] = transaction_date
    total_row["Merchant"] = merchant_name
    total_row["Item"] = "Total"
    total_row["Total"] = total_amount
    rows.append(total_row)

else:
    # No items found, create a single row with summary info
    row = {}
    for col in df_tpl.columns:
        row[col] = ""
    
    row["Date"] = transaction_date
    row["Merchant"] = merchant_name
    row["Total"] = total_amount
    rows.append(row)

# 7. Build output DataFrame
out_df = pd.DataFrame(rows)

# Clean up data types to avoid Arrow conversion issues
if not out_df.empty:
    # Convert Price column to numeric, replacing empty strings with 0
    if "Price" in out_df.columns:
        out_df["Price"] = pd.to_numeric(out_df["Price"], errors='coerce').fillna(0)
    
    # Convert Total column to numeric, replacing empty strings with 0
    if "Total" in out_df.columns:
        out_df["Total"] = pd.to_numeric(out_df["Total"], errors='coerce').fillna(0)
    
    # Ensure Date column is string
    if "Date" in out_df.columns:
        out_df["Date"] = out_df["Date"].astype(str)
    
    # Ensure Merchant and Item columns are strings
    if "Merchant" in out_df.columns:
        out_df["Merchant"] = out_df["Merchant"].astype(str)
    if "Item" in out_df.columns:
        out_df["Item"] = out_df["Item"].astype(str)

# 8. Display and download
st.subheader("3️⃣ Results")

# Show a preview of the extracted data
if not out_df.empty:
    st.success(f"✅ Extracted {len(out_df)} line items")
    
    # Mobile-friendly dataframe display
    st.dataframe(out_df, use_container_width=True)
    
    # Download section
    csv = out_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="receipt.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.warning("No data extracted from the receipt")

# Optional debug info (collapsed by default for cleaner mobile experience)
with st.expander("🔍 Debug Info (Advanced)"):
    st.write("**Available fields:**", list(fields.keys()))
    
    # Show all field values for debugging
    st.write("**All field values:**")
    for field_name, field_obj in fields.items():
        if hasattr(field_obj, 'value') and field_obj.value:
            st.write(f"- **{field_name}**: {field_obj.value}")
    
    if "Items" in fields:
        st.write("**Number of items found:**", len(fields["Items"].value) if fields["Items"].value else 0)
        if fields["Items"].value:
            st.write("**First item fields:**", list(fields["Items"].value[0].value.keys()))
            
            # Show detailed item information
            st.write("**Item details:**")
            for i, item in enumerate(fields["Items"].value[:3]):  # Show first 3 items
                st.write(f"Item {i+1}:")
                for field_name, field_obj in item.value.items():
                    if hasattr(field_obj, 'value') and field_obj.value:
                        st.write(f"  - {field_name}: {field_obj.value}")
                        
    # Show raw content preview if available
    if hasattr(res, 'content'):
        st.write("**Raw text content (first 500 chars):**")
        st.text(res.content[:500] + "..." if len(res.content) > 500 else res.content)
            
    st.write("**Extracted values:**")
    st.write(f"- **Merchant**: '{merchant_name}'")
    st.write(f"- **Date**: '{transaction_date}'")
    st.write(f"- **Total**: '{total_amount}'")
