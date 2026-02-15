"""
Vercel Python serverless function to handle file uploads and process them
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs
import cgi
import io

# Import processing logic
sys.path.insert(0, str(Path(__file__).parent))
from process_supabase_upload import process_file


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')

            if 'multipart/form-data' not in content_type:
                self.send_error(400, "Expected multipart/form-data")
                return

            # Parse the form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Create a file-like object from the POST data
            fp = io.BytesIO(post_data)

            # Parse the multipart form data
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': str(content_length),
            }

            form = cgi.FieldStorage(
                fp=fp,
                environ=environ,
                keep_blank_values=True
            )

            # Get the uploaded file
            if 'file' not in form:
                self.send_error(400, "No file uploaded")
                return

            file_item = form['file']

            if not file_item.file:
                self.send_error(400, "No file data")
                return

            # Validate file type
            filename = file_item.filename
            if not filename.endswith(('.xlsx', '.xls')):
                self.send_error(400, "Only Excel files (.xlsx, .xls) are supported")
                return

            # Save file to temp directory
            import datetime
            timestamp = datetime.datetime.now().isoformat().replace(':', '-').replace('.', '-')
            temp_filename = f"transaction-log-{timestamp}.xlsx"

            # Use /tmp for Vercel serverless
            temp_dir = '/tmp/uploads'
            os.makedirs(temp_dir, exist_ok=True)

            filepath = os.path.join(temp_dir, temp_filename)

            # Write the file
            with open(filepath, 'wb') as f:
                f.write(file_item.file.read())

            print(f"File saved: {filepath}", file=sys.stderr)

            # Process the file
            result = process_file(filepath)

            # Send response
            response_data = {
                'success': True,
                'filename': temp_filename,
                **result
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc()

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
