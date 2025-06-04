import boto3
import base64
import package.pymysql as pymysql
import google.generativeai as genai

# === Hardcoded Gemini API Key ===
GOOGLE_API_KEY = "AIzaSyCbYqEpHlbbxN53pDUufhW-HIc0j-lkRP0"

# === Configure Gemini API ===
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-pro-exp-02-05")

# === Caption generation helper ===
def generate_image_caption(image_data):
    try:
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": encoded_image},
            "Caption this image. Do not use bold or italics or other formatting"
        ])
        return response.text if response.text else "No caption generated."
    except Exception as e:
        return f"Error: {str(e)}"

# === Lambda handler ===
def lambda_handler(event, context):
    # Retrieve config from event
    s3_bucket = event['s3Bucket']
    s3_key = event['s3Key']
    s3_region = event['s3Region']

    db_host = event['dbHost']
    db_name = event['dbName']
    db_user = event['dbUser']
    db_password = event['dbPassword']

    # Step 1: Download image from S3
    try:
        s3 = boto3.client('s3', region_name=s3_region)
        image_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        image_data = image_obj['Body'].read()
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"S3 Error: {str(e)}"
        }

    # Step 2: Generate caption
    caption = generate_image_caption(image_data)
    if caption.startswith("Error:"):
        return {
            'statusCode': 500,
            'body': caption
        }

    # Step 3: Insert caption into RDS
    try:
        conn = pymysql.connect(
            host=db_host,
            user=db_user,
            passwd=db_password,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO captions (image_key, caption) VALUES (%s, %s)",
                (s3_key, caption)
            )
            conn.commit()
        conn.close()
    except pymysql.MySQLError as e:
        return {
            'statusCode': 500,
            'body': f"Database Error: {e.args[1]}"
        }

    # Return success response
    return {
        'statusCode': 200,
        'body': {
            'imageKey': s3_key,
            'caption': caption
        }
    }
