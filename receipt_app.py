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

# Upload option is always visible
img_upload = st.file_uploader("📁 Upload Image", type=["jpg","png","jpeg"])

# Camera option with toggle
use_camera = st.checkbox("📸 Use Camera Instead", help="Toggle to show camera input")
img_camera = None
if use_camera:
    img_camera = st.camera_input("� Take Photo")

img = img_camera or img_upload
if not img:
    st.info("📱 Upload a receipt image or use the camera to continue")
    st.stop()

# Display the uploaded/captured image as a thumbnail with expandable view
col1, col2 = st.columns([1, 3])
with col1:
    st.image(img, caption="📸 Receipt", width=150)
with col2:
    with st.expander("🔍 View Full Size Image"):
        st.image(img, caption="📸 Receipt Image", use_container_width=True)

# 3. Read image bytes
if hasattr(img, "read"):
    img_bytes = img.read()
else:
    buf = io.BytesIO()
    Image.open(img).save(buf, format="JPEG")
    img_bytes = buf.getvalue()

# 🚧 MAINTENANCE MODE - Azure processing temporarily disabled to avoid charges
st.warning("🚧 **Maintenance Mode**: Azure Form Recognizer processing is temporarily disabled to avoid charges. The app UI is working, but receipt parsing is paused.")
st.info("💡 You can still test the upload functionality and UI. Processing will be re-enabled when needed.")

# Show a sample CSV for demonstration
st.subheader("3️⃣ Results")
st.info("📋 This would normally show the extracted receipt data. Here's a sample of what the output would look like:")

# Create sample data matching the template
sample_data = {
    "Date": ["2024-01-15", "2024-01-15", "2024-01-15"],
    "Merchant": ["Sample Store", "Sample Store", "Sample Store"], 
    "Item": ["Coffee", "Sandwich", "Tax"],
    "Price": [4.50, 8.95, 1.25],
    "Total": ["", "", 14.70]
}

sample_df = pd.DataFrame(sample_data)
st.dataframe(sample_df, use_container_width=True)

# Provide download of sample data
csv = sample_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Sample CSV",
    data=csv,
    file_name="sample_receipt.csv",
    mime="text/csv",
    use_container_width=True,
    help="This is sample data - in normal mode, this would contain your actual receipt data"
)

st.stop()  # Stop execution here to avoid running Azure code



