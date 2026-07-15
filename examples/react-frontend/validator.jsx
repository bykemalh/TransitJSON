// React Client-Side / React Router Frontend Component
// This file runs inside the user's browser.
// Note: We only import the TransitJSONValidator (no database code) for zero-dependency client-side validation!

import React, { useState } from 'react';
// In your real project: import { TransitJSONValidator } from 'transit-json-js/validator';
// (Importing just the validator avoids bundling server-side db adapters in the client bundle!)
import { TransitJSONValidator } from '../../transit-json-js/validator';

export default function TransitJSONUpload() {
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target.result);
        
        // 1. Initialize validator on the client-side.
        // For browser usage, we can construct the validator with standard embedded schemas or fetch schemas.
        // If schemas are bundled, TransitJSONValidator can be instantiated directly.
        const validator = new TransitJSONValidator(); 
        
        // Let's assume we are uploading "stops" file
        validator.validate('stops', json);
        
        setValidationResult('✅ VALID: This file perfectly conforms to the TransitJSON Stops schema!');
        setError(null);
      } catch (err) {
        setValidationResult(null);
        setError(`❌ INVALID: ${err.message}`);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '500px', margin: 'auto' }}>
      <h2>TransitJSON Client-side Validator</h2>
      <p>Upload a TransitJSON <code>stops.json</code> file to validate its structure instantly in your browser before uploading:</p>
      
      <input type="file" accept=".json" onChange={handleFileUpload} style={{ marginBottom: '15px' }} />
      
      {validationResult && (
        <div style={{ color: 'green', backgroundColor: '#e6ffe6', padding: '10px', borderRadius: '4px', border: '1px solid green' }}>
          {validationResult}
        </div>
      )}
      
      {error && (
        <div style={{ color: 'red', backgroundColor: '#ffe6e6', padding: '10px', borderRadius: '4px', border: '1px solid red' }}>
          {error}
        </div>
      )}
    </div>
  );
}
