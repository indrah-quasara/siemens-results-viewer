import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
from PIL import Image, ImageDraw
import ast

# --- Sidebar: AWS Credentials ---
st.sidebar.title("AWS Settings")
bucket = st.sidebar.text_input("🪣 S3 Bucket", value="datasets-quasara-io")
region = st.sidebar.text_input("🌍 AWS Region", value="eu-central-1")

# --- Upload CSV ---
st.title("📄 Upload CSV with Image Paths and Coordinates")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    st.stop()  # Wait until CSV is uploaded before continuing


# --- Maintain state ---
if "index" not in st.session_state:
    st.session_state.index = 0

row = df.iloc[st.session_state.index]
filename = row["filename"]
score = row["confidence_score"]
object_key = row["s3_path"]

# Parse coordinates
try:
    coords = ast.literal_eval(row["coordinates"])
    if isinstance(coords[0], list):  # List of boxes
        boxes = coords
    else:
        boxes = [coords]
except Exception as e:
    boxes = []
    st.warning(f"Could not parse coordinates: {e}")

# --- Set up S3 client ---
try:
    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=st.secrets["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws_secret_access_key"]

    )

    s3_response = s3.get_object(Bucket=bucket, Key=object_key)
    image_data = s3_response["Body"].read()
    image = Image.open(BytesIO(image_data)).convert("RGB")
except Exception as e:
    st.error(f"❌ Could not load image from S3: {e}")
    st.stop()


# --- Display ---
st.title("🔍 S3 Image Viewer with Bounding Boxes")
st.markdown(f"### 🖼 Filename: `{filename}`")
st.image(image, caption=f"Confidence Score: {score}", use_column_width=True)

# --- Navigation ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⬅️ Previous") and st.session_state.index > 0:
        st.session_state.index -= 1
        st.rerun()

with col2:
    if st.button("➡️ Next") and st.session_state.index < len(df) - 1:
        st.session_state.index += 1
        st.rerun()

