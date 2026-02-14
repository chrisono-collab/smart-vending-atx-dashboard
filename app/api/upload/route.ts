import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json(
        { error: 'No file uploaded' },
        { status: 400 }
      );
    }

    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      return NextResponse.json(
        { error: 'Only Excel files (.xlsx, .xls) are supported' },
        { status: 400 }
      );
    }

    // Create uploads directory if it doesn't exist
    const uploadsDir = join(process.cwd(), 'uploads');
    await mkdir(uploadsDir, { recursive: true });

    // Save file with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `transaction-log-${timestamp}.xlsx`;
    const filepath = join(uploadsDir, filename);

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    await writeFile(filepath, buffer);

    console.log(`File saved: ${filepath}`);

    // Process the file using Python script
    console.log('Processing file...');
    const { stdout, stderr } = await execAsync(
      `cd "${process.cwd()}" && python process_supabase_upload.py "${filepath}"`,
      { maxBuffer: 10 * 1024 * 1024 } // 10MB buffer
    );

    console.log('Processing output:', stdout);
    if (stderr) console.error('Processing stderr:', stderr);

    // Parse the processing result from stdout
    const result = JSON.parse(stdout.trim().split('\n').pop() || '{}');

    return NextResponse.json({
      success: true,
      filename,
      ...result
    });

  } catch (error: any) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to process upload' },
      { status: 500 }
    );
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};
