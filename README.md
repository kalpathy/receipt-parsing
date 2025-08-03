# Receipt Parser App

A Streamlit application that uses Azure Form Recognizer to parse receipts and convert them to CSV format.

## Setup Instructions

### 1. Install Dependencies

First, make sure you have Python 3.7+ installed. Then install the required packages:

```bash
pip install -r requirements.txt
```

Or if you're using the virtual environment in this directory:

```bash
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Azure Credentials

You have two options for setting up your Azure Form Recognizer credentials:

#### Option A: Environment Variables (Recommended)
Set the environment variables in your terminal:

```bash
export AZURE_FORM_RECOGNIZER_ENDPOINT="https://your-resource-name.cognitiveservices.azure.com/"
export AZURE_FORM_RECOGNIZER_KEY="your_32_character_key_here"
```

#### Option B: .env File
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and replace the placeholder values with your actual Azure credentials:
   ```
   AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
   AZURE_FORM_RECOGNIZER_KEY=your_actual_key_here
   ```

### 3. Get Azure Form Recognizer Credentials

If you don't have Azure Form Recognizer set up yet:

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new "Form Recognizer" resource
3. Once created, go to "Keys and Endpoint" in the resource menu
4. Copy the endpoint URL and one of the keys

### 4. Run the Application

```bash
streamlit run receipt_app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. Upload a CSV template (or use the provided `template.csv`)
2. Take a photo of a receipt or upload a receipt image
3. The app will parse the receipt and display the results
4. Download the parsed data as CSV

## Files

- `receipt_app.py` - Main Streamlit application
- `template.csv` - Example CSV template with columns: Date, Merchant, Item, Price, Total
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment configuration file
- `receipt*.png` - Sample receipt images for testing

## Security Note

Never commit your `.env` file or actual credentials to version control. The `.env` file should be added to your `.gitignore`.
