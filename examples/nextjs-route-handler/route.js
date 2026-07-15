// Next.js App Router (Server-Side API Route Handler)
// Location: app/api/routes/route.js

import { NextResponse } from 'next/server';
import path from 'path';
import { TransitJSONDb } from 'transit-json-js';

// Initialize TransitJSONDb (This runs on Node.js environment in Next.js)
const dbPath = path.join(process.cwd(), 'data', 'transit.db');
const schemasDir = path.join(process.cwd(), 'schemas');
const db = new TransitJSONDb('sqlite', { dbPath, schemasDir });

// GET handler to retrieve routes
export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const agencyId = searchParams.get('agencyId');

  try {
    const routes = db.getRoutes(agencyId);
    return NextResponse.json({ success: true, data: routes });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// POST handler to dynamically import and validate live vehicles or data
export async function POST(request) {
  try {
    const body = await request.json();
    
    // Validate and load live vehicles feed
    db.importData('vehicles', body, true);
    
    return NextResponse.json({ success: true, message: 'Live vehicles successfully updated!' });
  } catch (error) {
    if (error.name === 'ValidationError') {
      return NextResponse.json({ success: false, error: 'Validation Error', details: error.message }, { status: 400 });
    }
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
