const express = require('express');
const path = require('path');
const { TransitJSONDb } = require('../../transit-json-js');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize database
const dbPath = path.join(__dirname, 'transit.db');
const schemasDir = path.join(__dirname, '..', '..', 'schemas');
const db = new TransitJSONDb('sqlite', { dbPath, schemasDir });

app.use(express.json());

// 1. Endpoint to upload and import a TransitJSON file (e.g. routes.json)
app.post('/api/import/:schema', (req, res) => {
  const schemaName = req.params.schema;
  const data = req.body;

  try {
    // Validates the incoming body against schema constraints and inserts it!
    db.importData(schemaName, data, true);
    res.json({ success: true, message: `${schemaName} data successfully validated and loaded into database!` });
  } catch (error) {
    if (error.name === 'ValidationError') {
      res.status(400).json({ success: false, error: 'Validation Failed', details: error.message });
    } else {
      res.status(500).json({ success: false, error: 'Internal Database Error', details: error.message });
    }
  }
});

// 2. Endpoint to query routes
app.get('/api/routes', (req, res) => {
  try {
    const agencyId = req.query.agencyId || null;
    const routes = db.getRoutes(agencyId);
    res.json({ success: true, count: routes.length, data: routes });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 3. Endpoint to query stops for a specific route
app.get('/api/routes/:routeId/stops', (req, res) => {
  const { routeId } = req.params;
  const { tripType } = req.query; // optional: outbound, inbound, loop
  try {
    const stops = db.getStops(routeId, tripType);
    res.json({ success: true, count: stops.length, data: stops });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`TransitJSON Express API running at http://localhost:${PORT}`);
});
